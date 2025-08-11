#!/usr/bin/env python3
"""
Comprehensive Human Language Training Data Generator
Covers all natural language patterns for email parsing
"""

import json
import random
from datetime import date, timedelta

def generate_comprehensive_training_data():
    """Generate comprehensive training data covering all human language patterns"""
    
    # Human language variations
    request_words = ["send", "please send", "kindly send", "share", "provide", "forward", "email", "give", "need", "want", "require", "request"]
    polite_words = ["please", "kindly", "could you", "can you", "would you", "may i", ""]
    urgency_words = ["urgent", "asap", "immediately", "priority", "rush", "quick", "fast", ""]
    
    # Statement variations
    statement_words = ["statement", "statements", "report", "reports", "soa", "document", "documents", "file", "files"]
    
    # Negation patterns
    negation_patterns = [
        "without {item}",
        "except {item}", 
        "excluding {item}",
        "not {item}",
        "no {item}",
        "minus {item}",
        "but not {item}"
    ]
    
    # Inclusion patterns  
    inclusion_patterns = [
        "with {item}",
        "including {item}",
        "plus {item}",
        "and {item}",
        "along with {item}",
        "together with {item}"
    ]
    
    # Time expressions
    time_expressions = [
        "as on {date}", "as at {date}", "for {date}", "on {date}",
        "from {from_date} to {to_date}", "between {from_date} and {to_date}",
        "for period {from_date} to {to_date}", "during {from_date} to {to_date}",
        "for FY {fy}", "for financial year {fy}", "for current FY", "for last FY",
        "for {period}", "for last {period}", "for current {period}", "for this {period}",
        "YTD", "MTD", "QTD", "year to date", "month to date", "quarter to date",
        "yesterday", "today", "last week", "this month", "last quarter"
    ]
    
    # Identifier patterns
    identifier_patterns = [
        "for PAN {pan}", "PAN {pan}", "pan number {pan}", "pan: {pan}",
        "for DI {di}", "DI {di}", "di code {di}", "di: {di}",
        "for account {account}", "account {account}", "account number {account}", "acc {account}",
        "for folio {folio}", "folio {folio}", "folio number {folio}", "aif folio {folio}"
    ]
    
    # Generate training samples
    training_data = []
    
    # 1. Basic request patterns
    for request in request_words:
        for polite in polite_words:
            for statement in statement_words:
                for urgency in urgency_words:
                    if random.random() < 0.1:  # 10% sample rate
                        text = f"{polite} {request} {statement} {urgency}".strip()
                        text = " ".join(text.split())  # Clean extra spaces
                        
                        training_data.append({
                            "text": text,
                            "labels": {
                                "statement_category": ["PMS"],
                                "statement_types": ["Portfolio_Appraisal"],
                                "confidence": random.uniform(70, 85)
                            }
                        })
    
    # 2. All statements patterns
    all_patterns = [
        "send all statements", "all reports", "everything", "complete statements",
        "send all pms statements", "all pms reports", "complete pms",
        "send all aif statements", "all aif reports", "complete aif"
    ]
    
    for pattern in all_patterns:
        for polite in ["please", "kindly", ""]:
            for urgency in ["urgent", "asap", ""]:
                text = f"{polite} {pattern} {urgency}".strip()
                text = " ".join(text.split())
                
                if "pms" in pattern:
                    category = ["PMS"]
                    statements = ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"]
                elif "aif" in pattern:
                    category = ["AIF"] 
                    statements = ["AIF_Statement"]
                else:
                    category = ["PMS", "AIF"]
                    statements = ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details", "AIF_Statement"]
                
                training_data.append({
                    "text": text,
                    "labels": {
                        "statement_category": category,
                        "statement_types": statements,
                        "confidence": random.uniform(85, 95)
                    }
                })
    
    # 3. Negation patterns
    base_requests = ["send all statements", "send all pms and aif statements", "provide complete reports"]
    
    for base in base_requests:
        for negation in negation_patterns:
            # Test negating AIF
            aif_negation = negation.format(item="aif")
            text = f"{base} {aif_negation}"
            
            training_data.append({
                "text": text,
                "labels": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"],
                    "confidence": random.uniform(80, 90)
                }
            })
            
            # Test negating PMS  
            pms_negation = negation.format(item="pms")
            text = f"{base} {pms_negation}"
            
            training_data.append({
                "text": text,
                "labels": {
                    "statement_category": ["AIF"],
                    "statement_types": ["AIF_Statement"],
                    "confidence": random.uniform(80, 90)
                }
            })
    
    # 4. Specific statement type requests
    specific_statements = {
        "soa": ["Portfolio_Appraisal"],
        "portfolio statement": ["Portfolio_Appraisal"], 
        "factsheet": ["Portfolio_Factsheet"],
        "performance report": ["Performance_Appraisal"],
        "transaction statement": ["Transaction_Statement"],
        "dividend statement": ["Statement_of_Dividend"],
        "aif statement": ["AIF_Statement"],
        "aif report": ["AIF_Statement"]
    }
    
    for stmt_text, stmt_types in specific_statements.items():
        for request in ["send", "provide", "share", "need"]:
            for polite in ["please", "kindly", ""]:
                text = f"{polite} {request} {stmt_text}".strip()
                text = " ".join(text.split())
                
                category = ["AIF"] if "aif" in stmt_text else ["PMS"]
                
                training_data.append({
                    "text": text,
                    "labels": {
                        "statement_category": category,
                        "statement_types": stmt_types,
                        "confidence": random.uniform(85, 95)
                    }
                })
    
    # 5. Complex combination patterns
    combinations = [
        ("send pms and aif statements", ["PMS", "AIF"], ["Portfolio_Appraisal", "AIF_Statement"]),
        ("need all pms without aif", ["PMS"], ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"]),
        ("provide everything except aif", ["PMS"], ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"]),
        ("send only pms statements", ["PMS"], ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"]),
        ("just aif reports", ["AIF"], ["AIF_Statement"])
    ]
    
    for text, category, statements in combinations:
        training_data.append({
            "text": text,
            "labels": {
                "statement_category": category,
                "statement_types": statements,
                "confidence": random.uniform(85, 95)
            }
        })
    
    # 6. Typos and informal language
    informal_patterns = [
        ("pls send soa", ["PMS"], ["Portfolio_Appraisal"]),
        ("need stmt asap", ["PMS"], ["Portfolio_Appraisal"]),
        ("send all rpts", ["PMS", "AIF"], ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details", "AIF_Statement"]),
        ("gimme portfolio stmt", ["PMS"], ["Portfolio_Appraisal"]),
        ("can u send aif", ["AIF"], ["AIF_Statement"])
    ]
    
    for text, category, statements in informal_patterns:
        training_data.append({
            "text": text,
            "labels": {
                "statement_category": category,
                "statement_types": statements,
                "confidence": random.uniform(75, 85)
            }
        })
    
    return training_data

def save_training_data():
    """Generate and save comprehensive training data"""
    data = generate_comprehensive_training_data()
    
    with open('training_data/human_language_training.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Generated {len(data)} comprehensive training samples")
    
    # Show distribution
    categories = {}
    for sample in data:
        for cat in sample['labels']['statement_category']:
            categories[cat] = categories.get(cat, 0) + 1
    
    print("Category distribution:")
    for cat, count in categories.items():
        print(f"  {cat}: {count}")

if __name__ == "__main__":
    import os
    os.makedirs('training_data', exist_ok=True)
    save_training_data()