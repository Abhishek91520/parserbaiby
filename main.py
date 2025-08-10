from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import logging
import os
from email_parser import IpruAIEmailParser
import json

# Configure enhanced logging
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

# File formatter (no colors)
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Console formatter (with colors)
console_formatter = ColoredFormatter(
    '🚀 %(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)

# Create logs directory if not exists
os.makedirs('logs', exist_ok=True)

# Daily log file with date
today = datetime.now().strftime('%Y-%m-%d')
log_filename = f'logs/ipruai_{today}.log'

# File handler with daily rotation
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setFormatter(file_formatter)
file_handler.setLevel(logging.DEBUG)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
console_handler.setLevel(logging.INFO)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[file_handler, console_handler]
)
logger = logging.getLogger('IpruAI')
logger.setLevel(logging.DEBUG)

app = FastAPI(title="IpruAI Email Parser API 🤖", version="1.0.0")
parser = IpruAIEmailParser()

class EmailRequest(BaseModel):
    subject: str
    body: str

class EmailResponse(BaseModel):
    statement_category: list
    statement_types: list
    aif_folio: list
    di_code: list
    account_code: list
    pan_numbers: list
    from_date: str
    to_date: str
    confidence: float
    metadata: dict
    raw_text: str
    success: bool
    processed_at: str

@app.post("/parse-email", response_model=EmailResponse)
async def parse_email(request: EmailRequest):
    try:
        start_time = datetime.now()
        
        # Combine subject and body
        full_text = f"Subject: {request.subject}\nBody: {request.body}"
        
        logger.info(f"📧 Processing email request")
        logger.debug(f"Subject: {request.subject}")
        logger.debug(f"Body length: {len(request.body)} chars")
        logger.debug(f"Log file: {log_filename}")
        
        # Parse email
        result = parser.parse_email(full_text)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        result['metadata']['processing_time_ms'] = round(processing_time, 2)
        result['processed_at'] = datetime.now().isoformat()
        result['success'] = True
        
        confidence_emoji = "💯" if result['confidence'] >= 80 else "🤔" if result['confidence'] >= 60 else "😅"
        logger.info(f"{confidence_emoji} Parsing completed - Confidence: {result['confidence']}% | Method: {result['metadata']['parsing_method']}")
        logger.debug(f"Categories: {result['statement_category']} | Types: {result['statement_types']}")
        logger.debug(f"Identifiers found: PAN={len(result['pan_numbers'])}, DI={len(result['di_code'])}, Accounts={len(result['account_code'])}, Folios={len(result['aif_folio'])}")
        logger.debug(f"Date range: {result['from_date']} to {result['to_date']} ({result['metadata']['date_source']})")
        
        return result
        
    except Exception as e:
        logger.error(f"😱 Error processing email: {str(e)}")
        logger.debug(f"Request details - Subject: {request.subject[:100]}, Body: {request.body[:200]}...")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "IpruAI Email Parser API 🤖",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test_parser():
    test_request = EmailRequest(
        subject="PMS Statement Request",
        body="Send me portfolio statement as on 15-Mar-2024 for PAN ABCDE1234F and DI D0131848"
    )
    return await parse_email(test_request)

if __name__ == "__main__":
    import uvicorn
    print("Starting IpruAI Email Parser API 🚀🤖")
    uvicorn.run(app, host="0.0.0.0", port=5000)