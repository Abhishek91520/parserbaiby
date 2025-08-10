import json
from email_parser import IpruAIEmailParser

def test_ipruai_parser():
    """Test the IpruAI email parser with various scenarios"""
    
    parser = IpruAIEmailParser()
    
    test_cases = [
        # High confidence cases
        {
            "name": "PMS with clear date",
            "input": "Subject: PMS Statement\nBody: Send me portfolio statement as on 15-Mar-2024 for PAN ABCDE1234F and DI D0131848",
            "expected_confidence": "> 80"
        },
        {
            "name": "AIF with folio",
            "input": "Subject: AIF Report\nBody: Please send AIF statement for folio 6700000071 as at 31-Dec-2023",
            "expected_confidence": "> 80"
        },
        {
            "name": "Mixed PMS+AIF",
            "input": "Subject: All Statements\nBody: Provide both PMS and AIF statements for PAN ABCDE1234F as on 31-Mar-2024",
            "expected_confidence": "> 80"
        },
        
        # Medium confidence cases
        {
            "name": "FY request",
            "input": "Subject: Annual Report\nBody: Send PMS statement for FY23-24 PAN ABCDE1234F",
            "expected_confidence": "70-85"
        },
        {
            "name": "Relative date",
            "input": "Subject: Recent Statement\nBody: Need portfolio for last 3 months PAN ABCDE1234F",
            "expected_confidence": "70-85"
        },
        
        # Low confidence cases (should trigger ML fallback)
        {
            "name": "Ambiguous request",
            "input": "Subject: Statement\nBody: Send statement for ABCDE1234F",
            "expected_confidence": "< 80 (ML fallback)"
        },
        {
            "name": "Unclear type",
            "input": "Subject: Report\nBody: Need report for PAN ABCDE1234F",
            "expected_confidence": "< 80 (ML fallback)"
        },
        
        # Edge cases
        {
            "name": "Multiple identifiers",
            "input": "Subject: Bulk Request\nBody: Send statements for PAN ABCDE1234F, FGHIJ5678K, DI D0131848, D9876543, accounts 10092344, 87654321, folios 6700000071, 8900000045",
            "expected_confidence": "> 80"
        },
        {
            "name": "No identifiers",
            "input": "Subject: Statement Request\nBody: Please send portfolio statement as on today",
            "expected_confidence": "Insufficient data"
        }
    ]
    
    print("Testing IpruAI Email Parser 🤖")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['name']}")
        print(f"Input: {test['input'][:80]}...")
        print(f"Expected: {test['expected_confidence']}")
        
        try:
            result = parser.parse_email(test['input'])
            
            confidence_emoji = "💯" if result['confidence'] >= 80 else "🤔" if result['confidence'] >= 60 else "😅"
            print(f"{confidence_emoji} Parsed successfully")
            print(f"   Categories: {result['statement_category']}")
            print(f"   Types: {result['statement_types']}")
            print(f"   PANs: {result['pan_numbers']}")
            print(f"   DI Codes: {result['di_code']}")
            print(f"   Accounts: {result['account_code']}")
            print(f"   AIF Folios: {result['aif_folio']}")
            print(f"   Dates: {result['from_date']} to {result['to_date']}")
            print(f"   Confidence: {result['confidence']}%")
            print(f"   Method: {result['metadata']['parsing_method']}")
            print(f"   Date Source: {result['metadata']['date_source']}")
            
        except Exception as e:
            print(f"😱 Error: {str(e)}")
        
        print("-" * 60)

def test_api_format():
    """Test API response format"""
    parser = IpruAIEmailParser()
    
    test_input = "Subject: PMS Statement\nBody: Send portfolio statement for PAN ABCDE1234F as on 15-Mar-2024"
    result = parser.parse_email(test_input)
    
    print("\nAPI Response Format Test:")
    print("=" * 30)
    print(json.dumps(result, indent=2))
    
    # Validate required fields
    required_fields = [
        'statement_category', 'statement_types', 'aif_folio', 'di_code',
        'account_code', 'pan_numbers', 'from_date', 'to_date', 'confidence',
        'metadata', 'raw_text'
    ]
    
    missing_fields = [field for field in required_fields if field not in result]
    
    if missing_fields:
        print(f"❌ Missing fields: {missing_fields}")
    else:
        print("✅ All required fields present")

if __name__ == "__main__":
    test_ipruai_parser()
    test_api_format()