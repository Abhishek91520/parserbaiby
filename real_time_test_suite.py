#!/usr/bin/env python3
"""
Real-time Test Suite - 100 Unique Hard Test Cases
Each test case represents actual user requests with expected vs actual results
"""

import json
import time
from datetime import datetime, date, timedelta
from email_parser import IpruAIEmailParser
import pandas as pd

class RealTimeTestSuite:
    def __init__(self):
        self.parser = IpruAIEmailParser()
        
    def get_hard_test_cases(self):
        """100 unique, challenging real-world test cases"""
        return [
            # 1-10: Basic AS ON patterns (most common)
            {"input": "Send SOA for PAN ABCDE1234F as on 15-Mar-2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-03-15"}},
            {"input": "pls provide statement for KLMNO5678G as on December 31, 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-12-31"}},
            {"input": "I need PMS report for DI D1234567 as on 25/08/2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-08-25"}},
            {"input": "Please send portfolio statement for account 12345678 as on 10.09.2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-09-10"}},
            {"input": "Share SOA for PAN PQRST9876H as on September 15, 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-09-15"}},
            {"input": "Send me statement for DI DI123456 as on 05-Nov-2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-11-05"}},
            {"input": "Portfolio report needed for UVWXY4321Z as on 20th October 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-10-20"}},
            {"input": "plz send statment for pan FGHIJ8765K as on Aug 12, 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-08-12"}},
            {"input": "I require PMS statement for DI D9876543 as on 30/12/2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-12-30"}},
            {"input": "Send portfolio appraisal for account 87654321 as on 01-Jan-2025", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-01-01"}},
            
            # 11-20: AIF statements with folios
            {"input": "AIF statement for folio 9000025789 as on 15-Mar-2024", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2024-03-15"}},
            {"input": "Please send AIF report for 8500067432 as on 25/08/2024", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2024-08-25"}},
            {"input": "I need Alternative Investment Fund statement for folio 7200045678", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-11"}},
            {"input": "AIF factsheet required for 6100089765 urgently", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-11"}},
            {"input": "Send AIF portfolio statement for folio 5900012345 as on 31-Dec-2024", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2024-12-31"}},
            {"input": "Alternative investment fund report for 8800054321 please", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-11"}},
            {"input": "I require AIF statement for PAN ABCDE1234F and folio 7700098765", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-11"}},
            {"input": "AIF report needed for folio 6600087654 for FY 23-24", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2023-04-01", "to_date": "2024-03-31"}},
            {"input": "Please provide AIF statement for 5500076543 as on 15/09/2024", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2024-09-15"}},
            {"input": "Send alternative investment fund factsheet for folio 8400065432", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-11"}},
            
            # 21-30: Date range patterns
            {"input": "Send statement for PAN KLMNO5678G from 01-Jan-2024 to 31-Mar-2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-01-01", "to_date": "2024-03-31"}},
            {"input": "Portfolio report for DI D1234567 from April 2024 to June 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-04-01", "to_date": "2024-06-30"}},
            {"input": "I need statement for account 12345678 between 15/07/2024 and 15/08/2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-07-15", "to_date": "2024-08-15"}},
            {"input": "AIF statement for folio 9000025789 from 01-Apr-2024 to 30-Sep-2024", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2024-04-01", "to_date": "2024-09-30"}},
            {"input": "Send SOA for PAN PQRST9876H for period from Jan 2024 to Dec 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-01-01", "to_date": "2024-12-31"}},
            {"input": "Portfolio statement for DI DI123456 from 1st March to 31st May 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-03-01", "to_date": "2024-05-31"}},
            {"input": "I require PMS report for UVWXY4321Z between Q1 and Q2 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-01-01", "to_date": "2024-06-30"}},
            {"input": "AIF factsheet for 8500067432 from beginning of FY to end of FY", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "Send statement for account 87654321 from last quarter", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-07-01", "to_date": "2024-09-30"}},
            {"input": "Portfolio appraisal for PAN FGHIJ8765K from 6 months ago to today", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-02-11", "to_date": "2025-08-11"}},
            
            # 31-40: Financial year patterns
            {"input": "Send all statements for PAN ABCDE1234F for FY 23-24", "expected": {"category": ["PMS"], "types": ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"], "from_date": "2023-04-01", "to_date": "2024-03-31"}},
            {"input": "I need PMS statements for DI D1234567 for financial year 2023-24", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2023-04-01", "to_date": "2024-03-31"}},
            {"input": "AIF report for folio 9000025789 for current financial year", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "Portfolio statement for account 12345678 for FY24", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "Send SOA for PAN KLMNO5678G for last financial year", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2023-04-01", "to_date": "2024-03-31"}},
            {"input": "I require statement for DI DI123456 for previous FY", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2023-04-01", "to_date": "2024-03-31"}},
            {"input": "AIF statement for 8500067432 for FY 2024-25", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "Portfolio report for PAN PQRST9876H for this FY", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "Send all PMS statements for account 87654321 for financial year 24-25", "expected": {"category": ["PMS"], "types": ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "I need AIF factsheet for folio 7200045678 for next financial year", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2025-04-01", "to_date": "2026-03-31"}},
            
            # 41-50: Multiple statement types
            {"input": "Send portfolio factsheet and transaction statement for PAN ABCDE1234F", "expected": {"category": ["PMS"], "types": ["Portfolio_Factsheet", "Transaction_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "I need performance appraisal and capital register for DI D1234567", "expected": {"category": ["PMS"], "types": ["Performance_Appraisal", "Capital_Register"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Please provide bank book and dividend statement for account 12345678", "expected": {"category": ["PMS"], "types": ["Bank_Book", "Statement_of_Dividend"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send transaction statement and expense statement for PAN KLMNO5678G", "expected": {"category": ["PMS"], "types": ["Transaction_Statement", "Statement_of_Expense"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "I require portfolio appraisal and client details for DI DI123456", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal", "Client_Details"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Portfolio factsheet, performance report and capital gain loss for PAN PQRST9876H", "expected": {"category": ["PMS"], "types": ["Portfolio_Factsheet", "Performance_Appraisal", "Statement_of_Capital_Gain_Loss"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send all transaction related statements for account 87654321", "expected": {"category": ["PMS"], "types": ["Transaction_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "I need complete portfolio and performance reports for DI D9876543", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal", "Performance_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Please provide dividend and expense statements for PAN UVWXY4321Z", "expected": {"category": ["PMS"], "types": ["Statement_of_Dividend", "Statement_of_Expense"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send bank book, capital register and client details for account 56789012", "expected": {"category": ["PMS"], "types": ["Bank_Book", "Capital_Register", "Client_Details"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            
            # 51-60: Casual/informal requests with typos
            {"input": "plz send soa for ABCDE1234F asap", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "need statment for D1234567 urgently", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "can u send portfolio report for 12345678 pls", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "i requir aif statment for 9000025789", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "pls provde pms report for KLMNO5678G", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "send me statemnts for DI123456 today", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "i ned aif report for folio 8500067432", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "plz share soa for account 87654321 asap", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "can you send me pms statment for PQRST9876H", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "i want aif factsheet for 7200045678 pls", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            
            # 61-70: Complex business scenarios
            {"input": "Please provide all PMS statements for PAN ABCDE1234F and DI D1234567 as on 15-Mar-2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Factsheet", "Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement", "Capital_Register", "Bank_Book", "Statement_of_Dividend", "Statement_of_Expense", "Statement_of_Capital_Gain_Loss", "Client_Details"], "from_date": "1990-01-01", "to_date": "2024-03-15"}},
            {"input": "I need complete portfolio analysis for multiple accounts: KLMNO5678G, D9876543, 12345678", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send quarterly performance report for PAN PQRST9876H for Q1 2024", "expected": {"category": ["PMS"], "types": ["Performance_Appraisal"], "from_date": "2024-01-01", "to_date": "2024-03-31"}},
            {"input": "AIF statement required for folio 9000025789 with PAN UVWXY4321Z for tax filing", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Please send year-end statements for DI DI123456 for FY closing", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-04-01", "to_date": "2025-03-31"}},
            {"input": "I require audit trail statements for account 87654321 from Apr to Sep 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-04-01", "to_date": "2024-09-30"}},
            {"input": "Send compliance report for AIF folio 8500067432 for regulatory submission", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Monthly portfolio summary for PAN FGHIJ8765K for last 6 months", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-02-11", "to_date": "2025-08-11"}},
            {"input": "Capital gains statement for DI D5555555 for ITR filing purpose", "expected": {"category": ["PMS"], "types": ["Statement_of_Capital_Gain_Loss"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Consolidated statement for all holdings under PAN ABCDE9999Z", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            
            # 71-80: Edge cases and tricky scenarios
            {"input": "Statement for 9000025789", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "ABCDE1234F report needed", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send everything for D1234567", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "12345678 statement please", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "I need SOA but have AIF folio 8500067432", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "AIF statement but using PAN KLMNO5678G", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Portfolio statement for AIF folio 7200045678", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send PMS report for AIF account 6100089765", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Statement as on yesterday for PQRST9876H", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Today's position for DI DI999999", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-11"}},
            
            # 81-90: Relative date patterns
            {"input": "Send statement for PAN ABCDE1234F for last 3 months", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-05-11", "to_date": "2025-08-11"}},
            {"input": "Portfolio report for DI D1234567 for past 6 months", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-02-11", "to_date": "2025-08-11"}},
            {"input": "I need AIF statement for 9000025789 for last quarter", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2025-04-01", "to_date": "2025-06-30"}},
            {"input": "Send SOA for account 12345678 for current month", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-08-01", "to_date": "2025-08-11"}},
            {"input": "Portfolio statement for KLMNO5678G for this year", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-01-01", "to_date": "2025-08-11"}},
            {"input": "AIF report for folio 8500067432 for previous month", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2025-07-01", "to_date": "2025-07-31"}},
            {"input": "I require statement for DI DI123456 for last week", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-08-04", "to_date": "2025-08-10"}},
            {"input": "Send portfolio report for PAN PQRST9876H for current quarter", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-07-01", "to_date": "2025-08-11"}},
            {"input": "Statement for account 87654321 for last 12 months", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2024-08-11", "to_date": "2025-08-11"}},
            {"input": "AIF factsheet for 7200045678 for year to date", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "2025-01-01", "to_date": "2025-08-11"}},
            
            # 91-100: Mixed and complex scenarios
            {"input": "Urgent: Send all statements for PAN ABCDE1234F, DI D1234567, and account 12345678", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "I need both PMS and AIF statements for KLMNO5678G and folio 9000025789", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Please send quarterly reports for all my accounts: PQRST9876H, D9876543, 87654321", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "2025-07-01", "to_date": "2025-08-11"}},
            {"input": "Tax filing documents needed for PAN UVWXY4321Z and AIF folio 8500067432", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Send me everything you have for FGHIJ8765K as on 31st March 2024", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2024-03-31"}},
            {"input": "I require complete financial summary for DI DI777777 for audit purpose", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Portfolio performance analysis for account 56789012 vs benchmark", "expected": {"category": ["PMS"], "types": ["Performance_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "AIF compliance report for folio 7200045678 for SEBI submission", "expected": {"category": ["AIF"], "types": ["AIF_Statement"], "from_date": "1990-01-01", "to_date": "2025-08-10"}},
            {"input": "Monthly P&L statement for PAN ABCDE9999Z for last financial year", "expected": {"category": ["PMS"], "types": ["Statement_of_Capital_Gain_Loss"], "from_date": "2023-04-01", "to_date": "2024-03-31"}},
            {"input": "Complete portfolio review for all holdings under DI D8888888 as on today", "expected": {"category": ["PMS"], "types": ["Portfolio_Appraisal"], "from_date": "1990-01-01", "to_date": "2025-08-11"}}
        ]
    
    def run_tests(self):
        """Run all test cases and generate results"""
        results = []
        total_time = 0
        
        print("Running 100 Real-time Test Cases...")
        print("=" * 60)
        
        test_cases = self.get_hard_test_cases()
        
        for i, test_case in enumerate(test_cases, 1):
            start_time = time.time()
            
            try:
                # Parse the input
                result = self.parser.parse_email(test_case["input"])
                processing_time = (time.time() - start_time) * 1000
                total_time += processing_time
                
                # Extract actual results
                actual = {
                    "category": result.get("statement_category", []),
                    "types": result.get("statement_types", []),
                    "from_date": result.get("from_date", ""),
                    "to_date": result.get("to_date", ""),
                    "confidence": result.get("confidence", 0),
                    "pan": result.get("pan_numbers", []),
                    "di": result.get("di_code", []),
                    "aif": result.get("aif_folio", []),
                    "account": result.get("account_code", [])
                }
                
                expected = test_case["expected"]
                
                # Check matches
                category_match = actual["category"] == expected["category"]
                type_match = set(actual["types"]) >= set(expected["types"])  # Actual can have more
                from_date_match = actual["from_date"] == expected["from_date"]
                to_date_match = actual["to_date"] == expected["to_date"]
                
                # Overall pass/fail
                status = "PASS" if (category_match and type_match and from_date_match and to_date_match) else "FAIL"
                
                # Issues
                issues = []
                if not category_match:
                    issues.append(f"Category: expected {expected['category']}, got {actual['category']}")
                if not type_match:
                    issues.append(f"Types: expected {expected['types']}, got {actual['types']}")
                if not from_date_match:
                    issues.append(f"From date: expected {expected['from_date']}, got {actual['from_date']}")
                if not to_date_match:
                    issues.append(f"To date: expected {expected['to_date']}, got {actual['to_date']}")
                
                results.append({
                    "Test_ID": i,
                    "Status": status,
                    "Input_Text": test_case["input"],
                    "Processing_Time_ms": round(processing_time, 2),
                    "Expected_Categories": expected["category"],
                    "Expected_Types": expected["types"],
                    "Expected_From_Date": expected["from_date"],
                    "Expected_To_Date": expected["to_date"],
                    "Actual_Categories": actual["category"],
                    "Actual_Types": actual["types"],
                    "Actual_From_Date": actual["from_date"],
                    "Actual_To_Date": actual["to_date"],
                    "Actual_Confidence": actual["confidence"],
                    "Actual_PAN": actual["pan"],
                    "Actual_DI": actual["di"],
                    "Actual_AIF": actual["aif"],
                    "Actual_Account": actual["account"],
                    "Issues": "; ".join(issues) if issues else "None",
                    "Category_Match": category_match,
                    "Statement_Type_Match": type_match,
                    "From_Date_Match": from_date_match,
                    "To_Date_Match": to_date_match
                })
                
                # Progress indicator
                if i % 10 == 0:
                    passed = sum(1 for r in results if r["Status"] == "PASS")
                    print(f"Completed {i}/100 tests. Pass rate: {passed/i*100:.1f}%")
                    
            except Exception as e:
                results.append({
                    "Test_ID": i,
                    "Status": "ERROR",
                    "Input_Text": test_case["input"],
                    "Processing_Time_ms": 0,
                    "Error": str(e),
                    "Issues": f"Exception: {str(e)}"
                })
        
        # Generate summary
        passed = sum(1 for r in results if r["Status"] == "PASS")
        failed = sum(1 for r in results if r["Status"] == "FAIL")
        errors = sum(1 for r in results if r["Status"] == "ERROR")
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Test Cases: 100")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Errors: {errors}")
        print(f"Pass Rate: {passed}%")
        print(f"Average Processing Time: {total_time/100:.2f}ms")
        print(f"Total Processing Time: {total_time:.2f}ms")
        
        # Save to Excel
        df = pd.DataFrame(results)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"real_time_test_results_{timestamp}.xlsx"
        df.to_excel(filename, index=False)
        print(f"\nResults saved to: {filename}")
        
        return results

if __name__ == "__main__":
    test_suite = RealTimeTestSuite()
    test_suite.run_tests()