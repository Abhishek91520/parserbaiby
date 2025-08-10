import time
import threading
import random
import pandas as pd
from datetime import datetime, timedelta
from email_parser import IpruAIEmailParser
import statistics
import json
import os

class DetailedStressTest:
    def __init__(self):
        self.parser = IpruAIEmailParser()
        
        # Test data pools
        self.pans = [f"{chr(65+i)}{chr(65+j)}{chr(65+k)}{chr(65+l)}{chr(65+m)}{random.randint(1000,9999)}{chr(65+n)}" 
                    for i in range(5) for j in range(5) for k in range(2) for l in range(2) for m in range(2) for n in range(2)][:200]
        
        self.di_codes = [f"D{random.randint(1000000,9999999)}" for _ in range(100)]
        self.accounts = [f"{random.randint(10000000,99999999)}" for _ in range(100)]
        self.aif_folios = [f"{random.choice([5,6,7,8,9])}{random.randint(100000000,999999999)}" for _ in range(100)]
        
        self.subjects = [
            "PMS Statement Request", "Portfolio Report", "AIF Statement", "Holdings Report",
            "Transaction Statement", "Performance Report", "Capital Register", "Bank Book",
            "Dividend Statement", "Expense Statement", "Client Details", "Annual Report"
        ]
        
        self.statement_keywords = [
            "portfolio statement", "pms statement", "soa", "holdings", "factsheet",
            "aif statement", "transaction statement", "performance report", "capital register",
            "bank book", "dividend statement", "expense statement", "client details"
        ]

    def generate_random_date(self):
        """Generate random date in various formats"""
        base_date = datetime.now() - timedelta(days=random.randint(1, 365))
        formats = ["%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%d %b %Y", "%d %B %Y"]
        return base_date.strftime(random.choice(formats))

    def generate_test_case(self, case_type="random"):
        """Generate tough Indian investor test cases"""
        subject = random.choice(self.subjects)
        
        if case_type == "high_confidence":
            pan = random.choice(self.pans)
            di_code = random.choice(self.di_codes)
            statement = random.choice(self.statement_keywords)
            
            # Tough Indian date formats
            indian_dates = [
                "15th March 2024", "23rd Dec 2024", "1st Jan 2025", "31st December 2024",
                "15-03-2024", "23/12/24", "01.01.2025", "31-Dec-24",
                "15 Mar 2024", "23 December 2024", "1 January 2025",
                "15032024", "23122024", "01012025",
                "March 15, 2024", "Dec 23, 2024", "January 1, 2025"
            ]
            date = random.choice(indian_dates)
            
            # Indian English variations
            templates = [
                f"Please send {statement} for PAN {pan} and DI {di_code} as on {date}",
                f"Kindly provide {statement} dated {date} for PAN {pan} DI {di_code}",
                f"Send me {statement} till {date} PAN {pan} and DI {di_code}",
                f"I need {statement} as at {date} for PAN {pan}, DI {di_code}",
                f"Please share {statement} on {date} for PAN {pan} & DI {di_code}"
            ]
            body = random.choice(templates)
            
            # Business logic: DI code = PMS, AIF folio = AIF
            # If both AIF statement requested AND DI code present = both PMS+AIF
            if "aif" in statement.lower() or "aif" in subject.lower():
                expected_category = ["PMS", "AIF"]  # DI code present, so PMS + AIF requested
            else:
                expected_category = ["PMS"]  # DI code present = PMS
            
            expected = {
                "confidence_range": (80, 100),
                "should_find_pan": True,
                "should_find_di": True,
                "should_find_date": True,
                "expected_category": expected_category
            }
            
        elif case_type == "aif_focused":
            folio = random.choice(self.aif_folios)
            pan = random.choice(self.pans)
            date = self.generate_random_date()
            body = f"Please provide AIF statement for folio {folio} and PAN {pan} as at {date}"
            expected = {
                "confidence_range": (80, 95),
                "should_find_pan": True,
                "should_find_aif_folio": True,
                "should_find_date": True,
                "expected_category": ["AIF"]
            }
            
        elif case_type == "mixed_identifiers":
            pan = random.choice(self.pans)
            di_code = random.choice(self.di_codes)
            account = random.choice(self.accounts)
            folio = random.choice(self.aif_folios)
            statement = random.choice(self.statement_keywords)
            date = self.generate_random_date()
            body = f"Send {statement} for PAN {pan}, DI {di_code}, account {account}, folio {folio} as on {date}"
            expected = {
                "confidence_range": (75, 90),
                "should_find_pan": True,
                "should_find_di": True,
                "should_find_account": True,
                "should_find_aif_folio": True,
                "should_find_date": True,
                "expected_category": ["PMS", "AIF"]
            }
            
        elif case_type == "low_confidence":
            pan = random.choice(self.pans)
            body = f"Send statement for {pan}"
            expected = {
                "confidence_range": (40, 70),
                "should_find_pan": True,
                "should_find_date": False,
                "expected_category": ["PMS"]
            }
            
        elif case_type == "extreme_dates":
            pan = random.choice(self.pans)
            di_code = random.choice(self.di_codes)
            statement = random.choice(self.statement_keywords)
            
            # Extreme English date formats that could break parsing
            extreme_dates = [
                "23rd December, 2024", "23-XII-2024", "Dec 23rd '24", "23/12/24",
                "2024-12-23T00:00:00Z", "23.12.2024", "December 23, 2024",
                "23 Dec 2024", "12/23/2024", "23-12-2024", "23/Dec/2024",
                "Dec-23-2024", "2024.12.23", "23 December 2024", "12-23-24",
                "23rd Dec '24", "December 23rd, 2024", "23/12/2024 10:30 AM",
                "23\12\2024", "23|12|2024", "DECEMBER 23, 2024", "23/XII/2024",
                "23 Dec 24", "23.XII.24", "23-Dec-24", "Dec 23, 24"
            ]
            date = random.choice(extreme_dates)
            body = f"Send {statement} for PAN {pan} DI {di_code} as on {date}"
            
            if "aif" in statement.lower() or "aif" in subject.lower():
                expected_category = ["PMS", "AIF"]
            else:
                expected_category = ["PMS"]
                
            expected = {
                "confidence_range": (60, 95),
                "should_find_pan": True,
                "should_find_di": True,
                "should_find_date": True,
                "expected_category": expected_category
            }
            
        elif case_type == "typos_and_errors":
            pan = random.choice(self.pans)
            di_code = random.choice(self.di_codes)
            date = self.generate_random_date()
            
            # Common typos and errors
            typo_templates = [
                f"Plese send portfollio statment for PAN {pan} DI {di_code} as on {date}",
                f"Send me PMS statemnt for PAN{pan} and DI{di_code} dated {date}",
                f"I need portflio report for PAN {pan}, DI {di_code} on {date}",
                f"Kindly provde statement for PAN {pan} & DI {di_code} as at {date}",
                f"Send PMS statmnt PAN {pan} DI {di_code} {date}"
            ]
            body = random.choice(typo_templates)
            
            if "aif" in body.lower() or "aif" in subject.lower():
                expected_category = ["PMS", "AIF"]
            else:
                expected_category = ["PMS"]
                
            expected = {
                "confidence_range": (70, 95),
                "should_find_pan": True,
                "should_find_di": True,
                "should_find_date": True,
                "expected_category": expected_category
            }
            
        elif case_type == "multiple_requests":
            pan1 = random.choice(self.pans)
            pan2 = random.choice(self.pans)
            di1 = random.choice(self.di_codes)
            di2 = random.choice(self.di_codes)
            date = self.generate_random_date()
            
            body = f"Send PMS statement for PAN {pan1} DI {di1} and also for PAN {pan2} DI {di2} as on {date}"
            
            if "aif" in body.lower() or "aif" in subject.lower():
                expected_category = ["PMS", "AIF"]
            else:
                expected_category = ["PMS"]
                
            expected = {
                "confidence_range": (75, 95),
                "should_find_pan": True,
                "should_find_di": True,
                "should_find_date": True,
                "expected_category": expected_category
            }
            
        elif case_type == "edge_cases":
            pan = random.choice(self.pans)
            
            # Edge cases that could break the system
            edge_templates = [
                f"PAN {pan} statement needed urgently!!!",
                f"Sir, please send statement for {pan} ASAP",
                f"Statement required for PAN {pan} - very urgent",
                f"Can you send PMS report for {pan}???",
                f"URGENT: Need statement for PAN {pan} immediately"
            ]
            body = random.choice(edge_templates)
            expected = {
                "confidence_range": (40, 80),
                "should_find_pan": True,
                "should_find_date": False,
                "expected_category": ["PMS"]
            }
            
        else:  # medium_confidence
            pan = random.choice(self.pans)
            statement = random.choice(self.statement_keywords[:5])
            body = f"Need {statement} for {pan} last quarter"
            expected = {
                "confidence_range": (60, 80),
                "should_find_pan": True,
                "should_find_date": True,
                "expected_category": ["PMS"]
            }
        
        return {
            "subject": subject,
            "body": body,
            "full_email": f"Subject: {subject}\nBody: {body}",
            "expected": expected,
            "type": case_type
        }

    def run_single_detailed_test(self, test_case, test_id):
        """Run a single test with detailed analysis"""
        start_time = time.time()
        
        try:
            result = self.parser.parse_email(test_case["full_email"])
            end_time = time.time()
            
            # Analyze results vs expectations
            analysis = self.analyze_test_result(test_case, result)
            
            return {
                "test_id": test_id,
                "test_type": test_case["type"],
                "input_email": {
                    "subject": test_case["subject"],
                    "body": test_case["body"],
                    "full_text": test_case["full_email"]
                },
                "expected_results": test_case["expected"],
                "actual_results": {
                    "confidence": result["confidence"],
                    "statement_category": result["statement_category"],
                    "statement_types": result["statement_types"],
                    "pan_numbers": result["pan_numbers"],
                    "di_code": result["di_code"],
                    "account_code": result["account_code"],
                    "aif_folio": result["aif_folio"],
                    "from_date": result["from_date"],
                    "to_date": result["to_date"],
                    "parsing_method": result["metadata"]["parsing_method"],
                    "date_source": result["metadata"]["date_source"]
                },
                "performance": {
                    "response_time_ms": (end_time - start_time) * 1000,
                    "success": True
                },
                "analysis": analysis,
                "overall_score": analysis["overall_score"]
            }
            
        except Exception as e:
            end_time = time.time()
            return {
                "test_id": test_id,
                "test_type": test_case["type"],
                "input_email": {
                    "subject": test_case["subject"],
                    "body": test_case["body"],
                    "full_text": test_case["full_email"]
                },
                "expected_results": test_case["expected"],
                "actual_results": None,
                "performance": {
                    "response_time_ms": (end_time - start_time) * 1000,
                    "success": False,
                    "error": str(e)
                },
                "analysis": {"overall_score": 0, "errors": [f"Parsing failed: {str(e)}"]},
                "overall_score": 0
            }

    def analyze_test_result(self, test_case, result):
        """Analyze test result against expectations"""
        expected = test_case["expected"]
        analysis = {
            "confidence_check": "PASS",
            "identifier_checks": [],
            "category_check": "PASS",
            "date_check": "PASS",
            "errors": [],
            "warnings": []
        }
        
        score = 100
        
        # Check confidence range
        conf_min, conf_max = expected["confidence_range"]
        if not (conf_min <= result["confidence"] <= conf_max):
            analysis["confidence_check"] = "FAIL"
            analysis["errors"].append(f"Confidence {result['confidence']}% not in expected range {conf_min}-{conf_max}%")
            score -= 20
        
        # Check identifiers
        if expected.get("should_find_pan", False):
            if len(result["pan_numbers"]) > 0:
                analysis["identifier_checks"].append("PAN: FOUND ✓")
            else:
                analysis["identifier_checks"].append("PAN: MISSING ✗")
                analysis["errors"].append("Expected to find PAN but didn't")
                score -= 15
        
        if expected.get("should_find_di", False):
            if len(result["di_code"]) > 0:
                analysis["identifier_checks"].append("DI: FOUND ✓")
            else:
                analysis["identifier_checks"].append("DI: MISSING ✗")
                analysis["errors"].append("Expected to find DI code but didn't")
                score -= 15
        
        if expected.get("should_find_account", False):
            if len(result["account_code"]) > 0:
                analysis["identifier_checks"].append("ACCOUNT: FOUND ✓")
            else:
                analysis["identifier_checks"].append("ACCOUNT: MISSING ✗")
                analysis["errors"].append("Expected to find account code but didn't")
                score -= 15
        
        if expected.get("should_find_aif_folio", False):
            if len(result["aif_folio"]) > 0:
                analysis["identifier_checks"].append("AIF_FOLIO: FOUND ✓")
            else:
                analysis["identifier_checks"].append("AIF_FOLIO: MISSING ✗")
                analysis["errors"].append("Expected to find AIF folio but didn't")
                score -= 15
        
        # Check categories
        expected_categories = set(expected.get("expected_category", []))
        actual_categories = set(result["statement_category"])
        
        if expected_categories != actual_categories:
            analysis["category_check"] = "FAIL"
            analysis["errors"].append(f"Expected categories {list(expected_categories)} but got {list(actual_categories)}")
            score -= 20
        
        # Check date extraction
        if expected.get("should_find_date", False):
            if result["metadata"]["date_source"] == "default":
                analysis["date_check"] = "FAIL"
                analysis["errors"].append("Expected to extract date from email but used default")
                score -= 10
        elif expected.get("should_find_date", True) == False:
            if result["metadata"]["date_source"] != "default":
                analysis["warnings"].append("Found date when not expected (not necessarily bad)")
        
        analysis["overall_score"] = max(0, score)
        return analysis

    def run_detailed_stress_test(self, num_tests=500):
        """Run detailed stress test with comprehensive logging"""
        print(f"🤖 IpruAI Detailed Stress Test - {num_tests} test cases")
        print("=" * 60)
        
        # Generate test cases
        print("📝 Generating detailed test cases...")
        test_cases = []
        
        # Extreme distribution for bulletproof testing
        distributions = {
            "high_confidence": int(num_tests * 0.15),
            "medium_confidence": int(num_tests * 0.1),
            "low_confidence": int(num_tests * 0.1),
            "mixed_identifiers": int(num_tests * 0.1),
            "aif_focused": int(num_tests * 0.1),
            "extreme_dates": int(num_tests * 0.15),
            "typos_and_errors": int(num_tests * 0.1),
            "multiple_requests": int(num_tests * 0.1),
            "edge_cases": int(num_tests * 0.1)
        }
        
        for case_type, count in distributions.items():
            for _ in range(count):
                test_cases.append(self.generate_test_case(case_type))
        
        print(f"✅ Generated {len(test_cases)} detailed test cases")
        
        # Run tests
        print(f"\n🚀 Running detailed analysis...")
        if len(test_cases) >= 50000:
            print(f"⚡ EXTREME SCALE: {len(test_cases):,} test cases - This may take several minutes...")
        
        start_time = time.time()
        
        results = []
        progress_interval = max(50, len(test_cases) // 100)  # Show progress every 1%
        
        for i, test_case in enumerate(test_cases, 1):
            result = self.run_single_detailed_test(test_case, i)
            results.append(result)
            
            if i % progress_interval == 0 or i == len(test_cases):
                elapsed = time.time() - start_time
                rate = i / elapsed if elapsed > 0 else 0
                eta = (len(test_cases) - i) / rate if rate > 0 else 0
                print(f"⏳ Progress: {i:,}/{len(test_cases):,} ({i/len(test_cases)*100:.1f}%) | Rate: {rate:.0f}/sec | ETA: {eta:.0f}s")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Generate reports
        self.generate_detailed_reports(results, total_time)
        
        return results

    def generate_detailed_reports(self, results, total_time):
        """Generate detailed Excel and JSON reports"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare data for Excel
        excel_data = []
        for result in results:
            row = {
                "Test_ID": result["test_id"],
                "Test_Type": result["test_type"],
                "Subject": result["input_email"]["subject"],
                "Body": result["input_email"]["body"],
                "Full_Email": result["input_email"]["full_text"],
                "Expected_Confidence_Min": result["expected_results"]["confidence_range"][0],
                "Expected_Confidence_Max": result["expected_results"]["confidence_range"][1],
                "Actual_Confidence": result["actual_results"]["confidence"] if result["actual_results"] else 0,
                "Expected_Categories": ", ".join(result["expected_results"].get("expected_category", [])),
                "Actual_Categories": ", ".join(result["actual_results"]["statement_category"]) if result["actual_results"] else "",
                "Statement_Types": ", ".join(result["actual_results"]["statement_types"]) if result["actual_results"] else "",
                "PAN_Found": ", ".join(result["actual_results"]["pan_numbers"]) if result["actual_results"] else "",
                "DI_Found": ", ".join(result["actual_results"]["di_code"]) if result["actual_results"] else "",
                "Account_Found": ", ".join(result["actual_results"]["account_code"]) if result["actual_results"] else "",
                "AIF_Folio_Found": ", ".join(result["actual_results"]["aif_folio"]) if result["actual_results"] else "",
                "From_Date": result["actual_results"]["from_date"] if result["actual_results"] else "",
                "To_Date": result["actual_results"]["to_date"] if result["actual_results"] else "",
                "Date_Source": result["actual_results"]["date_source"] if result["actual_results"] else "",
                "Parsing_Method": result["actual_results"]["parsing_method"] if result["actual_results"] else "",
                "Response_Time_MS": result["performance"]["response_time_ms"],
                "Success": result["performance"]["success"],
                "Overall_Score": result["overall_score"],
                "Confidence_Check": result["analysis"].get("confidence_check", "N/A"),
                "Category_Check": result["analysis"].get("category_check", "N/A"),
                "Date_Check": result["analysis"].get("date_check", "N/A"),
                "Identifier_Checks": "; ".join(result["analysis"].get("identifier_checks", [])),
                "Errors": "; ".join(result["analysis"].get("errors", [])),
                "Warnings": "; ".join(result["analysis"].get("warnings", []))
            }
            excel_data.append(row)
        
        # Create Excel file (limit to 1M rows for Excel compatibility)
        df = pd.DataFrame(excel_data)
        excel_filename = f"logs/detailed_stress_test_{timestamp}.xlsx"
        
        # For massive tests, create multiple Excel files or CSV
        if len(df) > 1000000:
            print(f"📊 Large dataset ({len(df):,} rows) - Creating CSV files instead of Excel...")
            csv_filename = f"logs/detailed_stress_test_{timestamp}.csv"
            df.to_csv(csv_filename, index=False)
            
            # Create summary Excel
            summary_data = self.create_summary_data(results, total_time)
            summary_df = pd.DataFrame([summary_data])
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
        else:
            with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
                # Main results sheet
                df.to_excel(writer, sheet_name='Test_Results', index=False)
                
                # Summary sheet
                summary_data = self.create_summary_data(results, total_time)
                summary_df = pd.DataFrame([summary_data])
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Failed tests sheet
                failed_tests = [r for r in results if r["overall_score"] < 70]
                if failed_tests:
                    failed_df = df[df['Overall_Score'] < 70]
                    failed_df.to_excel(writer, sheet_name='Failed_Tests', index=False)
        
        # Create detailed JSON report
        json_filename = f"logs/detailed_stress_test_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": self.create_summary_data(results, total_time),
                "detailed_results": results
            }, f, indent=2, ensure_ascii=False)
        
        # Print summary
        self.print_detailed_summary(results, total_time, excel_filename, json_filename)

    def create_summary_data(self, results, total_time):
        """Create summary statistics"""
        successful_tests = [r for r in results if r["performance"]["success"]]
        high_score_tests = [r for r in results if r["overall_score"] >= 80]
        medium_score_tests = [r for r in results if 60 <= r["overall_score"] < 80]
        low_score_tests = [r for r in results if r["overall_score"] < 60]
        
        return {
            "total_tests": len(results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(results) - len(successful_tests),
            "high_score_tests": len(high_score_tests),
            "medium_score_tests": len(medium_score_tests),
            "low_score_tests": len(low_score_tests),
            "avg_confidence": statistics.mean([r["actual_results"]["confidence"] for r in successful_tests]) if successful_tests else 0,
            "avg_response_time": statistics.mean([r["performance"]["response_time_ms"] for r in results]),
            "avg_overall_score": statistics.mean([r["overall_score"] for r in results]),
            "total_time_seconds": total_time,
            "throughput_per_second": len(successful_tests) / total_time if total_time > 0 else 0
        }

    def print_detailed_summary(self, results, total_time, excel_file, json_file):
        """Print detailed summary"""
        summary = self.create_summary_data(results, total_time)
        
        print(f"\n📊 Detailed Test Results Summary")
        print("=" * 60)
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Successful: {summary['successful_tests']} ({summary['successful_tests']/summary['total_tests']*100:.1f}%)")
        print(f"Failed: {summary['failed_tests']} ({summary['failed_tests']/summary['total_tests']*100:.1f}%)")
        print(f"\n🎯 Score Distribution:")
        print(f"High Score (≥80): {summary['high_score_tests']} ({summary['high_score_tests']/summary['total_tests']*100:.1f}%)")
        print(f"Medium Score (60-79): {summary['medium_score_tests']} ({summary['medium_score_tests']/summary['total_tests']*100:.1f}%)")
        print(f"Low Score (<60): {summary['low_score_tests']} ({summary['low_score_tests']/summary['total_tests']*100:.1f}%)")
        print(f"\n⚡ Performance:")
        print(f"Average Confidence: {summary['avg_confidence']:.1f}%")
        print(f"Average Response Time: {summary['avg_response_time']:.2f}ms")
        print(f"Average Overall Score: {summary['avg_overall_score']:.1f}")
        print(f"Throughput: {summary['throughput_per_second']:.1f} tests/second")
        print(f"\n📁 Reports Generated:")
        if len(results) > 1000000:
            print(f"📊 CSV Report: {excel_file.replace('.xlsx', '.csv')}")
            print(f"📊 Summary Excel: {excel_file}")
        else:
            print(f"📊 Excel Report: {excel_file}")
        print(f"📄 JSON Report: {json_file}")

def main():
    """Run detailed stress test"""
    tester = DetailedStressTest()
    
    print("🤖 IpruAI Detailed Stress Testing with Excel Reports")
    print("=" * 60)
    print("Choose test size:")
    print("1. Quick Test (100 cases)")
    print("2. Standard Test (500 cases)")
    print("3. Full Test (1000 cases)")
    print("4. Extreme Test (2000 cases)")
    print("5. Bulletproof Test (5000 cases)")
    print("6. Massive Test (50,000 cases)")
    print("7. Ultra Test (500,000 cases)")
    print("8. Ultimate Test (10,000,000 cases)")
    
    choice = input("\nEnter choice (1-8) or press Enter for Standard: ").strip()
    
    test_sizes = {"1": 100, "2": 500, "3": 1000, "4": 2000, "5": 5000, "6": 50000, "7": 500000, "8": 10000000}
    num_tests = test_sizes.get(choice, 500)
    
    if num_tests >= 50000:
        print(f"\n⚠️  WARNING: {num_tests:,} test cases will take significant time and resources!")
        confirm = input("Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            print("Test cancelled.")
            return
    
    print(f"\n🚀 Starting detailed stress test with {num_tests} cases...")
    results = tester.run_detailed_stress_test(num_tests)
    
    print(f"\n✅ Detailed stress test completed!")
    print("📊 Check the Excel file for comprehensive analysis with:")
    print("   • Full email content")
    print("   • Expected vs actual results")
    print("   • Detailed error analysis")
    print("   • Performance metrics")

if __name__ == "__main__":
    main()