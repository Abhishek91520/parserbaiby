# Email Parser API

A production-ready hybrid email parser that combines rule-based parsing with ML fallback for extracting financial statement requests from emails.

## Features

- **Hybrid Approach**: Rule-based parsing with ML fallback when confidence < 80%
- **High Accuracy**: Optimized for PMS and AIF statement extraction
- **FastAPI**: Modern, fast web framework with automatic documentation
- **Configurable**: JSON-based configuration for easy customization
- **Comprehensive Logging**: File-based logging with audit trail
- **Training Data**: 250+ synthetic samples for ML model training

## Quick Start

### 1. Setup Environment

```bash
# Run the automated setup
python setup.py
```

This will:
- Create virtual environment
- Install dependencies
- Generate training data
- Test the parser

### 2. Activate Environment

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Train ML Model (Optional)

```bash
python train_model.py
```

### 4. Start API Server

```bash
python main.py
```

The API will be available at `http://localhost:5000`

## API Usage

### Parse Email

**POST** `/parse-email`

```json
{
  "subject": "PMS Statement Request",
  "body": "Send me portfolio statement as on 15-Mar-2024 for PAN ABCDE1234F and DI D0131848"
}
```

**Response:**

```json
{
  "statement_category": ["PMS"],
  "statement_types": ["Portfolio_Appraisal"],
  "aif_folio": [],
  "di_code": ["D0131848"],
  "account_code": [],
  "pan_numbers": ["ABCDE1234F"],
  "from_date": "1990-01-01",
  "to_date": "2024-03-15",
  "confidence": 87.5,
  "metadata": {
    "date_source": "email",
    "parsing_method": "rule_based",
    "processing_time_ms": 25.3,
    "model_version": "1.0",
    "has_identifiers": true
  },
  "raw_text": "Subject: PMS Statement Request\nBody: Send me...",
  "success": true,
  "processed_at": "2024-01-15T10:30:00Z"
}
```

### Health Check

**GET** `/health`

### Test Endpoint

**GET** `/test`

## Supported Identifiers

| Type | Format | Example |
|------|--------|---------|
| PAN | AAAAA1234A | ABCDE1234F |
| DI Code | D1234567 | D0131848 |
| Account Code | 12345678 | 10092344 |
| AIF Folio | 5-9 + 9 digits | 6700000071 |

## Statement Types

### PMS Statements
- Portfolio_Factsheet
- Portfolio_Appraisal
- Performance_Appraisal
- Transaction_Statement
- Capital_Register
- Bank_Book
- Statement_of_Dividend
- Statement_of_Expense
- Statement_of_Capital_Gain_Loss
- Client_Details

### AIF Statements
- AIF_Statement

## Date Parsing

Supports various date formats:
- **As on dates**: "as on 15-Mar-2024"
- **Date ranges**: "from Jan 2024 to Mar 2024"
- **Financial years**: "FY23-24", "FY 2023-24"
- **Relative dates**: "last 3 months", "last quarter"
- **Default range**: 1990-01-01 to yesterday

## Configuration

### Regex Patterns (`config/regex_patterns.json`)
```json
{
  "identifiers": {
    "pan": "\\b[A-Z]{5}[0-9]{4}[A-Z]{1}\\b",
    "di_code": "\\bD[0-9A-Z]{7}\\b"
  }
}
```

### Statement Keywords (`config/statement_keywords.json`)
```json
{
  "pms": {
    "Portfolio_Appraisal": {
      "primary": ["soa", "pms statement"],
      "weight": 0.95
    }
  }
}
```

### Model Config (`config/model_config.json`)
```json
{
  "confidence_threshold": 80.0,
  "confidence_weights": {
    "statement_type": 0.4,
    "date_parsing": 0.4,
    "identifiers": 0.2
  }
}
```

## Training Your Own Model

### 1. Add Training Samples

Edit `training_data/generate_training_data.py` or add samples to `training_data/train_data.json`:

```json
{
  "text": "Subject: Statement\nBody: Send PMS statement for PAN ABCDE1234F",
  "labels": {
    "statement_category": ["PMS"],
    "statement_types": ["Portfolio_Appraisal"],
    "from_date": "1990-01-01",
    "to_date": "2024-01-15",
    "confidence": 85.0
  }
}
```

### 2. Retrain Model

```bash
python train_model.py
```

## Testing

```bash
# Run comprehensive tests
python test_parser.py

# Test specific scenarios
from email_parser import HybridEmailParser
parser = HybridEmailParser()
result = parser.parse_email("Your email text here")
```

## Confidence Scoring

- **High (80-100%)**: Clear statement type + date found
- **Medium (60-79%)**: Partial information, triggers ML fallback
- **Low (<60%)**: Ambiguous request, returns best guess

## Logging

Logs are written to `email_parser.log` with:
- Request details
- Parsing method used
- Confidence scores
- Processing times
- Errors and warnings

## Performance

- **Rule-based**: ~10-20ms per request
- **With ML fallback**: ~50-100ms per request
- **Memory usage**: ~300MB with ML model loaded

## Dependencies

- FastAPI 0.104.1
- Flair 0.13.1 (for ML)
- dateparser 1.2.0
- rapidfuzz 3.5.2
- python-dateutil 2.8.2

## Troubleshooting

### Common Issues

1. **ML model not loading**
   - Run `python train_model.py` to train the model
   - Check if `models/flair_model/final-model.pt` exists

2. **Low confidence scores**
   - Add more training samples
   - Adjust confidence weights in config
   - Check regex patterns match your data

3. **Date parsing issues**
   - Verify date formats in your emails
   - Add custom patterns to `regex_patterns.json`

### Debug Mode

Set logging level to DEBUG in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Add test cases to `test_parser.py`
2. Update configuration files for new patterns
3. Add training samples for edge cases
4. Test thoroughly before deployment

## License

MIT License - see LICENSE file for details.