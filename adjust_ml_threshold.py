#!/usr/bin/env python3
"""
ML Threshold Adjustment Utility
Allows easy adjustment of ML fallback threshold for production tuning
"""

import json
import logging
import argparse
from email_parser import IpruAIEmailParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_threshold():
    """Get current ML fallback threshold"""
    try:
        with open('config/model_config.json', 'r') as f:
            config = json.load(f)
        return config.get('ml_fallback_threshold', 60.0)
    except Exception as e:
        logger.error(f"Error reading config: {e}")
        return None

def set_threshold(new_threshold: float):
    """Set new ML fallback threshold"""
    try:
        # Validate threshold range
        with open('config/model_config.json', 'r') as f:
            config = json.load(f)
        
        min_threshold = config.get('production', {}).get('min_threshold', 30.0)
        max_threshold = config.get('production', {}).get('max_threshold', 80.0)
        
        if not (min_threshold <= new_threshold <= max_threshold):
            logger.error(f"Threshold must be between {min_threshold} and {max_threshold}")
            return False
        
        # Update threshold
        config['ml_fallback_threshold'] = new_threshold
        
        with open('config/model_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"ML fallback threshold updated to {new_threshold}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating threshold: {e}")
        return False

def test_threshold(threshold: float, test_cases: list = None):
    """Test the parser with a specific threshold"""
    if test_cases is None:
        test_cases = [
            "send statement",  # Low confidence case
            "Please send PMS statement for PAN ABCDE1234F",  # Medium confidence
            "I need portfolio appraisal for DI D0131848 as on 31-Mar-2024",  # High confidence
            "AIF report needed",  # Low confidence AIF case
            "all statements required"  # Ambiguous case
        ]
    
    # Temporarily set threshold
    original_threshold = get_current_threshold()
    set_threshold(threshold)
    
    try:
        # Test with new threshold
        parser = IpruAIEmailParser()
        
        logger.info(f"\nTesting with ML fallback threshold: {threshold}")
        logger.info("=" * 60)
        
        ml_fallback_count = 0
        
        for i, text in enumerate(test_cases, 1):
            logger.info(f"\nTest {i}: {text}")
            result = parser.parse_email(text)
            
            confidence = result['confidence']
            method = result['metadata']['parsing_method']
            ml_used = result['metadata']['ml_fallback_used']
            
            if ml_used:
                ml_fallback_count += 1
            
            logger.info(f"  Confidence: {confidence:.2f}")
            logger.info(f"  Method: {method}")
            logger.info(f"  ML Fallback: {'Yes' if ml_used else 'No'}")
            logger.info(f"  Statements: {result['statement_types']}")
        
        logger.info(f"\nSummary: {ml_fallback_count}/{len(test_cases)} cases used ML fallback")
        
    finally:
        # Restore original threshold
        if original_threshold is not None:
            set_threshold(original_threshold)

def main():
    parser = argparse.ArgumentParser(description='Adjust ML fallback threshold')
    parser.add_argument('--get', action='store_true', help='Get current threshold')
    parser.add_argument('--set', type=float, help='Set new threshold (30-80)')
    parser.add_argument('--test', type=float, help='Test with specific threshold')
    parser.add_argument('--optimize', action='store_true', help='Find optimal threshold')
    
    args = parser.parse_args()
    
    if args.get:
        threshold = get_current_threshold()
        if threshold is not None:
            print(f"Current ML fallback threshold: {threshold}")
        else:
            print("Error reading threshold")
    
    elif args.set:
        if set_threshold(args.set):
            print(f"Threshold set to {args.set}")
        else:
            print("Failed to set threshold")
    
    elif args.test:
        test_threshold(args.test)
    
    elif args.optimize:
        logger.info("Finding optimal threshold...")
        
        test_cases = [
            "send statement",
            "Please send PMS statement for PAN ABCDE1234F",
            "I need portfolio appraisal for DI D0131848 as on 31-Mar-2024",
            "AIF report needed",
            "all statements required",
            "pls send soa",
            "I need report for account 12345678",
            "Please provide AIF statement for folio 6700000071"
        ]
        
        best_threshold = 60.0
        best_score = 0
        
        for threshold in range(40, 81, 5):  # Test thresholds from 40 to 80
            logger.info(f"\nTesting threshold: {threshold}")
            
            # Set threshold temporarily
            original_threshold = get_current_threshold()
            set_threshold(threshold)
            
            try:
                parser = IpruAIEmailParser()
                total_confidence = 0
                ml_usage = 0
                
                for text in test_cases:
                    result = parser.parse_email(text)
                    total_confidence += result['confidence']
                    if result['metadata']['ml_fallback_used']:
                        ml_usage += 1
                
                avg_confidence = total_confidence / len(test_cases)
                ml_usage_rate = ml_usage / len(test_cases)
                
                # Score based on confidence and reasonable ML usage
                score = avg_confidence * (1 - abs(ml_usage_rate - 0.3))  # Target ~30% ML usage
                
                logger.info(f"  Avg Confidence: {avg_confidence:.2f}")
                logger.info(f"  ML Usage: {ml_usage_rate:.2%}")
                logger.info(f"  Score: {score:.2f}")
                
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
                    
            finally:
                # Restore original threshold
                if original_threshold is not None:
                    set_threshold(original_threshold)
        
        logger.info(f"\nOptimal threshold: {best_threshold} (score: {best_score:.2f})")
        
        # Ask if user wants to apply the optimal threshold
        response = input(f"Apply optimal threshold {best_threshold}? (y/n): ")
        if response.lower() == 'y':
            set_threshold(best_threshold)
            logger.info("Optimal threshold applied!")
    
    else:
        current = get_current_threshold()
        if current is not None:
            print(f"Current ML fallback threshold: {current}")
            print("\nUsage:")
            print("  --get          Get current threshold")
            print("  --set 65       Set threshold to 65")
            print("  --test 55      Test with threshold 55")
            print("  --optimize     Find optimal threshold")

if __name__ == "__main__":
    main()