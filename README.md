# Email Parser API

A production-ready hybrid email parser that combines rule-based parsing with ML enhancement for extracting financial statement requests from emails.

## Features

- **Hybrid Approach**: Rule-based parsing with ML enhancement when confidence < 60%
- **High Accuracy**: 95.7% ML accuracy with comprehensive business logic
- **FastAPI**: Modern, fast web framework with automatic documentation
- **Configurable**: JSON-based configuration for easy customization
- **Comprehensive Logging**: File-based logging with audit trail
- **Extensive Training**: 3,300+ training samples including synthetic data, human patterns, and date expressions

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

### 3. Train ML Model (Production)

```bash
python train_production_model.py
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

## Training Data System

### Comprehensive Training Data (3,300+ samples)

1. **Synthetic Data**: 2,003 samples covering business scenarios
2. **Human Language Patterns**: 831 samples with natural language variations
3. **Date Expressions**: 511 samples covering all date patterns

### Generate Training Data

```bash
# Generate human language patterns
python generate_human_training_data.py

# Generate date training data
python generate_date_training_data.py

# Train production model
python train_production_model.py
```

### Training Data Structure

```json
{
  "text": "Subject: Statement\nBody: Send PMS statement for PAN ABCDE1234F",
  "statement_category": ["PMS"],
  "statement_types": ["Portfolio_Appraisal"],
  "from_date": "1990-01-01",
  "to_date": "2024-01-15",
  "confidence": 85.0
}
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

## ML Enhancement System

### Confidence Thresholds
- **High (60-100%)**: Rule-based parsing sufficient
- **Medium (30-59%)**: ML enhancement triggered
- **Low (<30%)**: ML provides best-effort parsing

### ML Model Performance
- **Accuracy**: 95.7% on test data
- **Algorithm**: RandomForest with TfidfVectorizer
- **Features**: Text vectorization + engineered features
- **Training**: 3,300+ samples with cross-validation

### Threshold Adjustment
```bash
# Adjust ML fallback threshold (30-80%)
python adjust_ml_threshold.py --threshold 50
```

## Logging

Logs are written to `email_parser.log` with:
- Request details
- Parsing method used
- Confidence scores
- Processing times
- Errors and warnings

## Performance

- **Rule-based**: ~10-20ms per request
- **With ML enhancement**: ~30-60ms per request
- **Memory usage**: ~200MB with ML model loaded
- **ML Model**: RandomForest (faster than neural networks)
- **Accuracy**: 95.7% on comprehensive test dataset

## Dependencies

- FastAPI 0.104.1
- scikit-learn 1.3.0 (for ML)
- spacy 3.7.0 (for NLP)
- dateparser 1.2.0
- fuzzywuzzy 0.18.0
- python-dateutil 2.8.2
- joblib 1.3.0

## Troubleshooting

### Common Issues

1. **ML model not loading**
   - Run `python train_production_model.py` to train the model
   - Check if `models/spacy_model/model.joblib` exists

2. **Low confidence scores**
   - Generate more training data with specific patterns
   - Adjust ML threshold: `python adjust_ml_threshold.py --threshold 50`
   - Check regex patterns match your data

3. **Date parsing issues**
   - Run `python generate_date_training_data.py` for more date patterns
   - Verify date formats in your emails
   - Add custom patterns to `regex_patterns.json`

4. **Negation handling**
   - Current limitation: "no AIF", "only PMS" patterns need more training
   - System prioritizes positive detection over exclusion
   - Future enhancement: negation-specific training data

### Debug Mode

Set logging level to DEBUG in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## System Architecture

### Processing Flow
1. **Rule-based parsing**: Extract identifiers, dates, statement types
2. **Confidence calculation**: Based on extracted information quality
3. **ML enhancement**: Triggered when confidence < 60%
4. **Result merging**: Combine rule-based and ML results
5. **Business logic validation**: Apply priority rules and constraints

### Model Files
- `models/spacy_model/model.joblib`: Trained RandomForest model
- `models/spacy_model/vectorizer.joblib`: TfidfVectorizer
- `models/spacy_model/metadata.json`: Model metadata and performance

## Contributing

1. Add test cases to `test_parser.py`
2. Generate training data for new patterns
3. Update configuration files for new business rules
4. Test ML model performance after changes
5. Validate against production scenarios

## License

MIT License - see LICENSE file for details.