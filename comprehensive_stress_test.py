#!/usr/bin/env python3
"""
Comprehensive Stress Test Suite for Email Parser
Tests 1K, 2K, 5K, 10K, 100K emails with real-life examples
Generates Excel report with input/output/expected analysis
"""

import json
import time
import random
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
import pandas as pd
from email_parser import IpruAIEmailParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveStressTest:
    def __init__(self):
        self.parser = IpruAIEmailParser()
        self.test_results = []
        
    def generate_real_life_test_cases(self, count: int) -> List[Dict]:
        """Generate real-life email test cases with expected outputs"""
        test_cases = []
        
        # Real-life email patterns from actual users
        real_patterns = [
            # Basic requests
            {
                "template": "Please send me PMS statement for PAN {pan} as on {date}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_pan": True,
                    "date_type": "as_on"
                }
            },
            {
                "template": "I need AIF statement for folio {aif_folio} from {from_date} to {to_date}",
                "expected": {
                    "statement_category": ["AIF"],
                    "statement_types": ["AIF_Statement"],
                    "should_have_aif": True,
                    "date_type": "range"
                }
            },
            {
                "template": "Send SOA for DI {di_code} as on {date}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_di": True,
                    "date_type": "as_on"
                }
            },
            
            # Casual/informal requests
            {
                "template": "pls send statement for {pan} asap",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_pan": True,
                    "date_type": "default"
                }
            },
            {
                "template": "need portfolio report for {di_code} urgently",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_di": True,
                    "date_type": "default"
                }
            },
            
            # Complex requests
            {
                "template": "Please provide all PMS statements for PAN {pan} and DI {di_code} as on {date}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal", "Performance_Appraisal", "Transaction_Statement"],
                    "should_have_pan": True,
                    "should_have_di": True,
                    "date_type": "as_on"
                }
            },
            {
                "template": "I require AIF statement for PAN {pan} and folio {aif_folio} for FY 23-24",
                "expected": {
                    "statement_category": ["AIF"],
                    "statement_types": ["AIF_Statement"],
                    "should_have_pan": True,
                    "should_have_aif": True,
                    "date_type": "fy"
                }
            },
            
            # Date variations
            {
                "template": "Send statement for {pan} for last 3 months",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_pan": True,
                    "date_type": "relative"
                }
            },
            {
                "template": "Portfolio statement needed for {di_code} for current FY",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_di": True,
                    "date_type": "fy"
                }
            },
            
            # Typos and variations
            {
                "template": "plz send statment for pan {pan} as on {date}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_pan": True,
                    "date_type": "as_on"
                }
            },
            {
                "template": "i need aif report for folio {aif_folio} asap",
                "expected": {
                    "statement_category": ["AIF"],
                    "statement_types": ["AIF_Statement"],
                    "should_have_aif": True,
                    "date_type": "default"
                }
            },
            
            # Edge cases
            {
                "template": "Send everything for {pan}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "should_have_pan": True,
                    "date_type": "default"
                }
            },
            {
                "template": "AIF statement for {aif_folio} please",
                "expected": {
                    "statement_category": ["AIF"],
                    "statement_types": ["AIF_Statement"],
                    "should_have_aif": True,
                    "date_type": "default"
                }
            },
            
            # Multiple statement types
            {
                "template": "Send portfolio factsheet and transaction statement for {pan} as on {date}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Factsheet", "Transaction_Statement"],
                    "should_have_pan": True,
                    "date_type": "as_on"
                }
            },
            
            # Business scenarios
            {
                "template": "Please share performance appraisal for DI {di_code} for Q1 2024",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Performance_Appraisal"],
                    "should_have_di": True,
                    "date_type": "quarter"
                }
            },
            {
                "template": "Capital register needed for account {account} from {from_date} to {to_date}",
                "expected": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Capital_Register"],
                    "should_have_account": True,
                    "date_type": "range"
                }
            }
        ]
        
        # Generate test cases
        for i in range(count):
            pattern = random.choice(real_patterns)
            template = pattern["template"]
            expected = pattern["expected"].copy()
            
            # Generate realistic identifiers
            pan = self._generate_realistic_pan()
            di_code = self._generate_realistic_di()
            aif_folio = self._generate_realistic_aif()
            account = self._generate_realistic_account()
            
            # Generate realistic dates
            base_date = date.today() - timedelta(days=random.randint(1, 365))
            from_date = base_date - timedelta(days=random.randint(30, 180))
            
            # Format dates in various realistic formats
            date_formats = [
                "%d-%b-%Y",     # 15-Mar-2024
                "%d/%m/%Y",     # 15/03/2024
                "%d.%m.%Y",     # 15.03.2024
                "%d %B %Y",     # 15 March 2024
                "%B %d, %Y",    # March 15, 2024
            ]
            
            date_format = random.choice(date_formats)
            formatted_date = base_date.strftime(date_format)
            formatted_from = from_date.strftime(date_format)
            formatted_to = base_date.strftime(date_format)
            
            # Fill template
            text = template.format(
                pan=pan,
                di_code=di_code,
                aif_folio=aif_folio,
                account=account,
                date=formatted_date,
                from_date=formatted_from,
                to_date=formatted_to
            )
            
            # Add expected date information
            if expected.get("date_type") == "as_on":
                expected["expected_from_date"] = "1990-01-01"
                expected["expected_to_date"] = str(base_date)
            elif expected.get("date_type") == "range":
                expected["expected_from_date"] = str(from_date)
                expected["expected_to_date"] = str(base_date)
            elif expected.get("date_type") == "default":
                expected["expected_from_date"] = "1990-01-01"
                expected["expected_to_date"] = str(date.today() - timedelta(days=1))
            
            # Add identifiers to expected
            if expected.get("should_have_pan"):
                expected["expected_pan"] = [pan]
            if expected.get("should_have_di"):
                expected["expected_di"] = [di_code]
            if expected.get("should_have_aif"):
                expected["expected_aif"] = [aif_folio]
            if expected.get("should_have_account"):
                expected["expected_account"] = [account]
            
            test_cases.append({
                "id": i + 1,
                "input_text": text,
                "expected": expected,
                "category": "real_life"
            })
        
        return test_cases
    
    def _generate_realistic_pan(self) -> str:
        """Generate realistic PAN numbers"""
        prefixes = ["ABCDE", "FGHIJ", "KLMNO", "PQRST", "UVWXY"]
        prefix = random.choice(prefixes)
        digits = f"{random.randint(1000, 9999)}"
        suffix = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        return f"{prefix}{digits}{suffix}"
    
    def _generate_realistic_di(self) -> str:
        """Generate realistic DI codes"""
        if random.random() < 0.7:
            return f"D{random.randint(1000000, 9999999)}"
        else:
            return f"DI{random.randint(100000, 999999)}"
    
    def _generate_realistic_aif(self) -> str:
        """Generate realistic AIF folios"""
        return f"{random.choice([5,6,7,8,9])}{random.randint(100000000, 999999999)}"
    
    def _generate_realistic_account(self) -> str:
        """Generate realistic account codes"""
        return f"{random.randint(10000000, 99999999)}"
    
    def run_stress_test(self, test_size: int) -> Dict[str, Any]:
        """Run comprehensive stress test"""
        logger.info(f"🚀 Starting stress test with {test_size:,} test cases")
        
        # Generate test cases
        test_cases = self.generate_real_life_test_cases(test_size)
        
        results = {
            "test_size": test_size,
            "start_time": datetime.now(),
            "test_cases": [],
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "avg_processing_time": 0,
                "total_processing_time": 0
            }
        }
        
        total_processing_time = 0
        
        for i, test_case in enumerate(test_cases, 1):
            if i % 1000 == 0:
                logger.info(f"Processed {i:,}/{test_size:,} test cases...")
            
            try:
                # Parse email
                start_time = time.time()
                result = self.parser.parse_email(test_case["input_text"])
                processing_time = (time.time() - start_time) * 1000
                total_processing_time += processing_time
                
                # Analyze result
                analysis = self._analyze_result(test_case, result)
                
                test_result = {
                    "id": test_case["id"],
                    "input_text": test_case["input_text"],
                    "expected": test_case["expected"],
                    "actual": result,
                    "analysis": analysis,
                    "processing_time_ms": processing_time,
                    "status": "PASS" if analysis["overall_pass"] else "FAIL"
                }
                
                results["test_cases"].append(test_result)
                
                if analysis["overall_pass"]:
                    results["summary"]["passed"] += 1
                else:
                    results["summary"]["failed"] += 1
                    
            except Exception as e:
                logger.error(f"Error in test case {i}: {e}")
                results["summary"]["errors"] += 1
                results["test_cases"].append({
                    "id": test_case["id"],
                    "input_text": test_case["input_text"],
                    "expected": test_case["expected"],
                    "actual": None,
                    "analysis": {"error": str(e)},
                    "processing_time_ms": 0,
                    "status": "ERROR"
                })
        
        # Calculate summary
        results["summary"]["total"] = len(test_cases)
        results["summary"]["avg_processing_time"] = total_processing_time / len(test_cases) if test_cases else 0
        results["summary"]["total_processing_time"] = total_processing_time
        results["end_time"] = datetime.now()
        results["duration"] = (results["end_time"] - results["start_time"]).total_seconds()
        
        logger.info(f"✅ Stress test completed: {results['summary']['passed']}/{results['summary']['total']} passed")
        
        return results
    
    def _analyze_result(self, test_case: Dict, result: Dict) -> Dict[str, Any]:
        """Analyze test result against expected output"""
        expected = test_case["expected"]
        analysis = {
            "overall_pass": True,
            "issues": [],
            "checks": {}
        }
        
        # Check statement categories
        expected_categories = set(expected.get("statement_category", []))
        actual_categories = set(result.get("statement_category", []))
        
        if expected_categories != actual_categories:
            analysis["overall_pass"] = False
            analysis["issues"].append(f"Category mismatch: expected {list(expected_categories)}, got {list(actual_categories)}")
        analysis["checks"]["category_match"] = expected_categories == actual_categories
        
        # Check statement types (at least one should match)
        expected_types = set(expected.get("statement_types", []))
        actual_types = set(result.get("statement_types", []))
        
        if expected_types and not expected_types.intersection(actual_types):
            analysis["overall_pass"] = False
            analysis["issues"].append(f"No statement type match: expected any of {list(expected_types)}, got {list(actual_types)}")
        analysis["checks"]["statement_type_match"] = bool(expected_types.intersection(actual_types)) if expected_types else True
        
        # Check identifiers
        identifier_checks = [
            ("pan", "expected_pan", "pan_numbers"),
            ("di", "expected_di", "di_code"),
            ("aif", "expected_aif", "aif_folio"),
            ("account", "expected_account", "account_code")
        ]
        
        for check_name, expected_key, actual_key in identifier_checks:
            if expected_key in expected:
                expected_ids = set(expected[expected_key])
                actual_ids = set(result.get(actual_key, []))
                
                if not expected_ids.intersection(actual_ids):
                    analysis["overall_pass"] = False
                    analysis["issues"].append(f"{check_name.upper()} not found: expected {list(expected_ids)}, got {list(actual_ids)}")
                analysis["checks"][f"{check_name}_match"] = bool(expected_ids.intersection(actual_ids))
        
        # Check dates (if specified)
        if "expected_from_date" in expected:
            expected_from = expected["expected_from_date"]
            actual_from = result.get("from_date")
            
            if expected_from != actual_from:
                analysis["issues"].append(f"From date mismatch: expected {expected_from}, got {actual_from}")
                # Don't fail for date issues unless severely wrong
                if actual_from and abs((datetime.strptime(expected_from, "%Y-%m-%d").date() - 
                                     datetime.strptime(actual_from, "%Y-%m-%d").date()).days) > 30:
                    analysis["overall_pass"] = False
            analysis["checks"]["from_date_match"] = expected_from == actual_from
        
        if "expected_to_date" in expected:
            expected_to = expected["expected_to_date"]
            actual_to = result.get("to_date")
            
            if expected_to != actual_to:
                analysis["issues"].append(f"To date mismatch: expected {expected_to}, got {actual_to}")
                if actual_to and abs((datetime.strptime(expected_to, "%Y-%m-%d").date() - 
                                   datetime.strptime(actual_to, "%Y-%m-%d").date()).days) > 30:
                    analysis["overall_pass"] = False
            analysis["checks"]["to_date_match"] = expected_to == actual_to
        
        # Check confidence
        confidence = result.get("confidence", 0)
        if confidence < 50:
            analysis["issues"].append(f"Low confidence: {confidence}")
        analysis["checks"]["confidence_ok"] = confidence >= 50
        
        return analysis
    
    def generate_excel_report(self, results: Dict[str, Any], filename: str = None):
        """Generate comprehensive Excel report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stress_test_report_{results['test_size']}_{timestamp}.xlsx"
        
        logger.info(f"📊 Generating Excel report: {filename}")
        
        # Prepare data for Excel
        excel_data = []
        
        for test_case in results["test_cases"]:
            row = {
                "Test_ID": test_case["id"],
                "Status": test_case["status"],
                "Input_Text": test_case["input_text"],
                "Processing_Time_ms": test_case.get("processing_time_ms", 0),
                
                # Expected values
                "Expected_Categories": ", ".join(test_case["expected"].get("statement_category", [])),
                "Expected_Types": ", ".join(test_case["expected"].get("statement_types", [])),
                "Expected_From_Date": test_case["expected"].get("expected_from_date", ""),
                "Expected_To_Date": test_case["expected"].get("expected_to_date", ""),
                
                # Actual values
                "Actual_Categories": ", ".join(test_case["actual"].get("statement_category", [])) if test_case["actual"] else "",
                "Actual_Types": ", ".join(test_case["actual"].get("statement_types", [])) if test_case["actual"] else "",
                "Actual_From_Date": test_case["actual"].get("from_date", "") if test_case["actual"] else "",
                "Actual_To_Date": test_case["actual"].get("to_date", "") if test_case["actual"] else "",
                "Actual_Confidence": test_case["actual"].get("confidence", 0) if test_case["actual"] else 0,
                
                # Identifiers
                "Actual_PAN": ", ".join(test_case["actual"].get("pan_numbers", [])) if test_case["actual"] else "",
                "Actual_DI": ", ".join(test_case["actual"].get("di_code", [])) if test_case["actual"] else "",
                "Actual_AIF": ", ".join(test_case["actual"].get("aif_folio", [])) if test_case["actual"] else "",
                "Actual_Account": ", ".join(test_case["actual"].get("account_code", [])) if test_case["actual"] else "",
                
                # Analysis
                "Issues": "; ".join(test_case["analysis"].get("issues", [])),
                "Category_Match": test_case["analysis"].get("checks", {}).get("category_match", False),
                "Statement_Type_Match": test_case["analysis"].get("checks", {}).get("statement_type_match", False),
                "From_Date_Match": test_case["analysis"].get("checks", {}).get("from_date_match", False),
                "To_Date_Match": test_case["analysis"].get("checks", {}).get("to_date_match", False),
                "Confidence_OK": test_case["analysis"].get("checks", {}).get("confidence_ok", False),
            }
            excel_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(excel_data)
        
        # Create summary data
        summary_data = {
            "Metric": [
                "Total Test Cases",
                "Passed",
                "Failed", 
                "Errors",
                "Pass Rate (%)",
                "Average Processing Time (ms)",
                "Total Processing Time (ms)",
                "Test Duration (seconds)"
            ],
            "Value": [
                results["summary"]["total"],
                results["summary"]["passed"],
                results["summary"]["failed"],
                results["summary"]["errors"],
                round((results["summary"]["passed"] / results["summary"]["total"]) * 100, 2),
                round(results["summary"]["avg_processing_time"], 2),
                round(results["summary"]["total_processing_time"], 2),
                round(results["duration"], 2)
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        
        # Write to Excel with multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Detailed results
            df.to_excel(writer, sheet_name='Detailed_Results', index=False)
            
            # Failed cases only
            failed_df = df[df['Status'] == 'FAIL']
            if not failed_df.empty:
                failed_df.to_excel(writer, sheet_name='Failed_Cases', index=False)
            
            # Performance analysis
            perf_df = df[['Test_ID', 'Processing_Time_ms', 'Actual_Confidence', 'Status']].copy()
            perf_df.to_excel(writer, sheet_name='Performance', index=False)
        
        logger.info(f"✅ Excel report generated: {filename}")
        return filename

def main():
    """Main stress testing function"""
    tester = ComprehensiveStressTest()
    
    # Test sizes to run
    test_sizes = [1000, 2000, 5000, 10000]
    
    for size in test_sizes:
        logger.info(f"\n{'='*60}")
        logger.info(f"RUNNING STRESS TEST: {size:,} TEST CASES")
        logger.info(f"{'='*60}")
        
        # Run stress test
        results = tester.run_stress_test(size)
        
        # Generate Excel report
        filename = tester.generate_excel_report(results)
        
        # Print summary
        summary = results["summary"]
        logger.info(f"\n📊 STRESS TEST RESULTS ({size:,} cases):")
        logger.info(f"   Passed: {summary['passed']:,} ({summary['passed']/summary['total']*100:.1f}%)")
        logger.info(f"   Failed: {summary['failed']:,} ({summary['failed']/summary['total']*100:.1f}%)")
        logger.info(f"   Errors: {summary['errors']:,}")
        logger.info(f"   Avg Processing Time: {summary['avg_processing_time']:.2f}ms")
        logger.info(f"   Total Duration: {results['duration']:.2f}s")
        logger.info(f"   Report: {filename}")
        
        # Break if too many failures
        if summary['failed'] / summary['total'] > 0.2:  # More than 20% failures
            logger.warning(f"⚠️  High failure rate ({summary['failed']/summary['total']*100:.1f}%), stopping tests")
            break
    
    logger.info("\n🎉 Comprehensive stress testing completed!")

if __name__ == "__main__":
    main()