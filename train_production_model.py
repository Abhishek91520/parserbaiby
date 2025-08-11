#!/usr/bin/env python3
"""
Production-ready ML Model Trainer for Email Parser
Comprehensive training with enhanced features and validation
"""

import json
import os
import logging
from typing import List, Dict, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib
from email_parser import IpruAIEmailParser
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionMLTrainer:
    def __init__(self):
        self.parser = IpruAIEmailParser()
        self.vectorizer = TfidfVectorizer(
            max_features=8000,  # Increased for better feature coverage
            ngram_range=(1, 4),  # Include 4-grams for better phrase capture
            stop_words='english',
            min_df=2,  # Ignore terms that appear in less than 2 documents
            max_df=0.95,  # Ignore terms that appear in more than 95% of documents
            sublinear_tf=True  # Use sublinear tf scaling
        )
        self.model = MultiOutputClassifier(
            RandomForestClassifier(
                n_estimators=200,  # Increased for better performance
                max_depth=15,  # Prevent overfitting
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1,
                class_weight='balanced'  # Handle class imbalance
            )
        )
        self.label_names = None
        
    def prepare_training_data(self, size: int = 2000) -> Tuple[List[str], np.ndarray, List[str]]:
        """Generate and prepare comprehensive training data"""
        logger.info(f"Generating {size} training samples...")
        
        # Generate synthetic data
        training_data = self.parser.generate_training_data(size)
        
        # Prepare features and labels
        texts = []
        labels = []
        
        # Get all possible statement types
        pms_types = list(self.parser.statement_keywords["pms"].keys())
        self.label_names = pms_types + ["AIF_Statement"]
        
        logger.info(f"Training for {len(self.label_names)} statement types: {self.label_names}")
        
        for i, sample in enumerate(training_data):
            try:
                text = sample["text"]
                sample_labels = sample["labels"]
                
                # Extract features using the parser's method
                identifiers = self.parser.extract_identifiers(text)
                features = self.parser._extract_ml_features(text, identifiers)
                texts.append(features)
                
                # Create multi-label output vector
                label_vector = [0] * len(self.label_names)
                
                # Set labels based on statement types
                stmt_types_list = sample_labels.get("statement_types", [])
                if not isinstance(stmt_types_list, list):
                    stmt_types_list = [stmt_types_list] if stmt_types_list else []
                
                for stmt_type in stmt_types_list:
                    if stmt_type in self.label_names:
                        idx = self.label_names.index(stmt_type)
                        label_vector[idx] = 1
                
                labels.append(label_vector)
                
            except Exception as e:
                logger.error(f"Error processing sample {i}: {e}")
                continue
        
        logger.info(f"Prepared {len(texts)} training samples")
        return texts, np.array(labels), self.label_names
    
    def train_model(self, size: int = 2000, test_size: float = 0.2):
        """Train the production ML model with comprehensive evaluation"""
        logger.info("Starting production ML model training...")
        
        # Prepare data
        texts, labels, label_names = self.prepare_training_data(size)
        
        # Vectorize features
        logger.info("Vectorizing features...")
        X = self.vectorizer.fit_transform(texts)
        logger.info(f"Feature matrix shape: {X.shape}")
        
        # Split data (remove stratify due to class imbalance)
        X_train, X_test, y_train, y_test = train_test_split(
            X, labels, test_size=test_size, random_state=42
        )
        
        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        # Train model
        logger.info("Training model...")
        self.model.fit(X_train, y_train)
        
        # Evaluate on test set
        logger.info("Evaluating model...")
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)
        
        # Calculate metrics for each statement type
        results = {}
        overall_accuracy = 0
        valid_classes = 0
        
        for i, stmt_type in enumerate(label_names):
            support = np.sum(y_test[:, i])
            
            if support > 0:  # Only calculate metrics for classes with test samples
                accuracy = accuracy_score(y_test[:, i], y_pred[:, i])
                f1 = f1_score(y_test[:, i], y_pred[:, i], average='binary', zero_division=0)
                
                results[stmt_type] = {
                    'accuracy': accuracy,
                    'f1_score': f1,
                    'support': support
                }
                
                logger.info(f"{stmt_type:25} - Accuracy: {accuracy:.3f}, F1: {f1:.3f}, Support: {support}")
                overall_accuracy += accuracy
                valid_classes += 1
            else:
                logger.info(f"{stmt_type:25} - No test samples")
                results[stmt_type] = {
                    'accuracy': 0.0,
                    'f1_score': 0.0,
                    'support': 0
                }
        
        if valid_classes > 0:
            overall_accuracy /= valid_classes
        else:
            overall_accuracy = 0.0
        logger.info(f"Overall accuracy: {overall_accuracy:.3f}")
        
        # Cross-validation for robustness check (only for classes with enough samples)
        logger.info("Performing cross-validation...")
        cv_scores = []
        for i in range(min(3, len(label_names))):
            # Check if class has enough samples for CV
            if np.sum(y_train[:, i]) >= 3:  # Need at least 3 samples for 3-fold CV
                try:
                    scores = cross_val_score(
                        RandomForestClassifier(n_estimators=50, random_state=42),
                        X_train, y_train[:, i], cv=3, scoring='f1'
                    )
                    cv_scores.append(np.mean(scores))
                    logger.info(f"CV F1 for {label_names[i]}: {np.mean(scores):.3f} (+/- {np.std(scores) * 2:.3f})")
                except Exception as e:
                    logger.warning(f"CV failed for {label_names[i]}: {e}")
            else:
                logger.info(f"Skipping CV for {label_names[i]} - insufficient samples ({np.sum(y_train[:, i])})")
        
        # Feature importance analysis
        self.analyze_feature_importance()
        
        return overall_accuracy, results
    
    def analyze_feature_importance(self):
        """Analyze and log feature importance"""
        try:
            feature_names = self.vectorizer.get_feature_names_out()
            
            # Get feature importance from the first estimator (they should be similar)
            importances = self.model.estimators_[0].feature_importances_
            
            # Get top 20 most important features
            top_indices = np.argsort(importances)[-20:]
            top_features = [(feature_names[i], importances[i]) for i in top_indices]
            top_features.reverse()
            
            logger.info("Top 20 most important features:")
            for feature, importance in top_features:
                logger.info(f"  {feature:30} - {importance:.4f}")
                
        except Exception as e:
            logger.warning(f"Feature importance analysis failed: {e}")
    
    def save_model(self, model_path: str = "models/spacy_model"):
        """Save trained model and components"""
        os.makedirs(model_path, exist_ok=True)
        
        # Save model and vectorizer
        joblib.dump(self.model, f"{model_path}/model.joblib")
        joblib.dump(self.vectorizer, f"{model_path}/vectorizer.joblib")
        
        # Save metadata
        metadata = {
            "model_type": "RandomForest_MultiOutput_Production",
            "vectorizer_type": "TfidfVectorizer_Enhanced",
            "features": "text + identifiers + spacy_entities + ngrams",
            "outputs": self.label_names,
            "training_size": self.parser.model_config["training"]["dataset_size"],
            "training_date": datetime.now().isoformat(),
            "model_version": "2.0_production",
            "vectorizer_params": {
                "max_features": 8000,
                "ngram_range": [1, 4],
                "min_df": 2,
                "max_df": 0.95
            },
            "model_params": {
                "n_estimators": 200,
                "max_depth": 15,
                "min_samples_split": 5,
                "min_samples_leaf": 2
            }
        }
        
        with open(f"{model_path}/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Production model saved to {model_path}")
    
    def test_model_scenarios(self):
        """Test the trained model with realistic scenarios"""
        test_cases = [
            # Basic PMS requests
            "Please send me PMS statement for PAN ABCDE1234F as on 31-Mar-2024",
            "I need portfolio appraisal for DI D0131848 from Jan-2024 to Mar-2024",
            "Send SOA for account 12345678 as on yesterday",
            
            # AIF requests
            "Please provide AIF statement for folio 6700000071 as on 31-Mar-2024",
            "I need AIF report for PAN ABCDE1234F and folio 6700000071",
            
            # Period-based requests
            "Send PMS statement for FY 23-24 for PAN ABCDE1234F",
            "I need all statements for last quarter for DI D0131848",
            "Please provide portfolio statement for YTD",
            
            # Multiple statements
            "Send all PMS statements for PAN ABCDE1234F",
            "I need complete statements for DI D0131848 and PAN ABCDE1234F",
            
            # Edge cases
            "pls send soa asap",
            "AIF needed",
            "all reports required",
            
            # Ambiguous cases (should trigger ML fallback)
            "send statement",
            "I need report for account",
            "please provide details"
        ]
        
        logger.info("Testing model with realistic scenarios...")
        
        for i, text in enumerate(test_cases, 1):
            logger.info(f"\nTest Case {i}: {text}")
            
            try:
                # Test with the parser (which will use ML fallback if needed)
                result = self.parser.parse_email(text)
                
                logger.info(f"  Confidence: {result['confidence']:.2f}")
                logger.info(f"  Method: {result['metadata']['parsing_method']}")
                logger.info(f"  Statement types: {result['statement_types']}")
                logger.info(f"  Categories: {result['statement_category']}")
                logger.info(f"  ML fallback used: {result['metadata']['ml_fallback_used']}")
                
            except Exception as e:
                logger.error(f"  Error: {e}")

def main():
    """Main training function"""
    logger.info("Starting production ML model training...")
    
    trainer = ProductionMLTrainer()
    
    # Train model with larger dataset
    dataset_size = trainer.parser.model_config["training"]["dataset_size"]
    accuracy, results = trainer.train_model(size=dataset_size)
    
    # Save model
    trainer.save_model()
    
    # Test model
    trainer.test_model_scenarios()
    
    logger.info(f"Production training completed with accuracy: {accuracy:.3f}")
    logger.info("Model ready for production use!")
    
    # Update model config to reflect production readiness
    config_path = "config/model_config.json"
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    config["version"] = "2.0_production"
    config["last_trained"] = datetime.now().isoformat()
    config["production_ready"] = True
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info("Model configuration updated for production use")

if __name__ == "__main__":
    main()