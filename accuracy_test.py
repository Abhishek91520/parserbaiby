#!/usr/bin/env python3
"""Quick accuracy test for enhanced email parser"""

from email_parser import IpruAIEmailParser

def test_enhanced_accuracy():
    parser = IpruAIEmailParser()
    
    # Test cases from the stress test that had lower scores
    test_cases = [
        {
            "text": "Please send client details for PAN BABBB3999A and DI D9494417 as on 31-Dec-24",
            "expected_confidence": 95
        },
        {
            "text": "Send me transaction statement till 01.01.2025 PAN CBBAA3733A and DI D8126629", 
            "expected_confidence": 95
        },
        {
            "text": "Please send factsheet for PAN AEBBA4401A and DI D5845180 as on 01012025",
            "expected_confidence": 95
        },
        {
            "text": "Please share pms statement on 15 Mar 2024 for PAN ABABA8323A & DI D2935832",
            "expected_confidence": 95
        }
    ]
    
    total_confidence = 0
    for i, case in enumerate(test_cases, 1):
        result = parser.parse_email(case["text"])
        confidence = result["confidence"]
        total_confidence += confidence
        
        print(f"Test {i}: {confidence}% (Expected: {case['expected_confidence']}%)")
        print(f"  Statement Types: {result['statement_types']}")
        print(f"  PAN: {result['pan_numbers']}")
        print(f"  DI: {result['di_code']}")
        print(f"  Date Range: {result['from_date']} to {result['to_date']}")
        print()
    
    avg_confidence = total_confidence / len(test_cases)
    print(f"Average Confidence: {avg_confidence:.2f}%")
    print(f"Target: 99%")
    print(f"Improvement: {avg_confidence - 83.96:.2f}% from baseline")

if __name__ == "__main__":
    test_enhanced_accuracy()