import re
import json
import logging
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fuzzywuzzy import fuzz
import dateparser
import datefinder
from typing import Dict, List, Tuple, Optional, Any
import spacy
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
import joblib


logger = logging.getLogger('IpruAI.Parser')

class IpruAIEmailParser:
    def __init__(self):
        self.load_configs()
        self.DEFAULT_FROM_DATE = datetime(1990, 1, 1).date()
        self._compile_regex_patterns()
        self.ml_model = None
        self.vectorizer = None
        self.nlp = None
        self._load_ml_model()
        
    def load_configs(self):
        """Load configuration files"""
        try:
            with open('config/regex_patterns.json', 'r') as f:
                self.regex_patterns = json.load(f)
            with open('config/statement_keywords.json', 'r') as f:
                self.statement_keywords = json.load(f)
            with open('config/model_config.json', 'r') as f:
                self.model_config = json.load(f)
        except Exception as e:
            logger.error(f"Error loading configs: {e}")
            raise
    
    def _compile_regex_patterns(self):
        """Compile regex patterns for better performance"""
        self.compiled_patterns = {}
        for category, patterns in self.regex_patterns.items():
            if isinstance(patterns, dict):
                self.compiled_patterns[category] = {}
                for key, pattern in patterns.items():
                    if isinstance(pattern, list):
                        # For lists of patterns, compile each one
                        self.compiled_patterns[category][key] = [re.compile(p) for p in pattern]
                    else:
                        # For single patterns, compile directly
                        self.compiled_patterns[category][key] = re.compile(pattern)
            else:
                self.compiled_patterns[category] = re.compile(patterns)
    
    def _load_ml_model(self):
        """Load ML model and components for fallback"""
        try:
            model_path = self.model_config["ml_model"]["model_path"]
            if os.path.exists(f"{model_path}/model.joblib") and os.path.exists(f"{model_path}/vectorizer.joblib"):
                self.ml_model = joblib.load(f"{model_path}/model.joblib")
                self.vectorizer = joblib.load(f"{model_path}/vectorizer.joblib")
                logger.info("ML model loaded successfully")
            
            # Load spaCy model
            spacy_model = self.model_config["ml_model"]["spacy_model"]
            try:
                self.nlp = spacy.load(spacy_model)
                logger.info(f"spaCy model {spacy_model} loaded successfully")
            except OSError:
                logger.warning(f"spaCy model {spacy_model} not found. ML fallback will be limited.")
                self.nlp = None
        except Exception as e:
            logger.warning(f"ML model loading failed: {e}. Using rule-based only.")
            self.ml_model = None
            self.vectorizer = None

    def extract_identifiers(self, text: str) -> Dict[str, List[str]]:
        """Extract PAN, DI codes, Account IDs, and AIF folios"""
        text_upper = text.upper()
        
        # Enhanced PAN extraction with context validation
        pan_pattern = self.compiled_patterns["identifiers"]["pan"]
        pan_matches = pan_pattern.findall(text_upper)
        pans = list(set([pan for pan in pan_matches if self._validate_pan(pan)]))
        
        # Enhanced DI code extraction
        di_pattern = self.compiled_patterns["identifiers"]["di_code"]
        di_matches = di_pattern.findall(text_upper)
        false_positives = {
            'DECEMBER', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER',
            'DIVIDEND', 'DOCUMENT', 'DELIVERY', 'DIRECTOR', 'DETAILED', 'DOWNLOAD', 'DOMESTIC', 'DURATION', 'DIFFERENT', 'DIRECTLY'
        }
        di_codes = list(set([di for di in di_matches if di not in false_positives and self._validate_di_code(di, text_upper)]))
        
        # AIF folios: 10 digits starting with 5,6,7,8,9
        aif_pattern = self.compiled_patterns["identifiers"]["aif_folio"]
        aif_folios = list(set(aif_pattern.findall(text)))
        
        # Account codes: exactly 8 digit numbers (excluding AIF folios and dates)
        account_pattern = self.compiled_patterns["identifiers"]["account_code"]
        all_8_digits = set(account_pattern.findall(text))
        aif_folio_strings = set(aif_folios)
        
        # Filter out date patterns (DDMMYYYY, YYYYMMDD)
        date_patterns = set()
        for digit_str in all_8_digits:
            if len(digit_str) == 8:
                # Check if it looks like DDMMYYYY or YYYYMMDD
                if (digit_str[:2] in ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31'] and 
                    digit_str[2:4] in ['01','02','03','04','05','06','07','08','09','10','11','12']) or \
                   (digit_str[:4] in ['2020','2021','2022','2023','2024','2025','2026','2027','2028','2029','2030']):
                    date_patterns.add(digit_str)
        
        account_codes = list(all_8_digits - aif_folio_strings - date_patterns)
        
        return {
            "pan_numbers": pans,
            "di_code": di_codes,
            "aif_folio": aif_folios,
            "account_code": account_codes
        }
    
    def _validate_pan(self, pan: str) -> bool:
        """Validate PAN format"""
        if len(pan) != 10:
            return False
        # Check format: 5 letters + 4 digits + 1 letter
        return pan[:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()
    
    def _validate_di_code(self, di: str, context: str) -> bool:
        """Validate DI code with proper format checking"""
        if not re.match(r'^D[0-9A-Z]{7}$|^DI[0-9A-Z]{6}$', di):
            return False
        
        # Check for financial context
        financial_context = ['SEND', 'STATEMENT', 'PORTFOLIO', 'REPORT', 'PLEASE', 'FOR', 'ACCOUNT', 'FOLIO', 'CLIENT', 'PAN']
        if any(indicator in context for indicator in financial_context):
            return True
        
        # Additional validation: check if it's not a common false positive
        return len(di) in [8, 9] and di.startswith('D')

    def match_statement_types(self, text: str) -> Tuple[List[str], List[str], float]:
        """Enhanced statement type matching with multi-layer scoring"""
        text_lower = text.lower()
        pms_statements = []
        aif_statements = []
        max_confidence = 0.0
        
        # Enhanced AIF detection with context scoring (check first)
        aif_score = 0
        for keyword in self.statement_keywords["aif"]["AIF_Statement"]["primary"]:
            if keyword in text_lower:
                aif_score = max(aif_score, 95.0)
        for keyword in self.statement_keywords["aif"]["AIF_Statement"]["secondary"]:
            if keyword in text_lower:
                aif_score = max(aif_score, 85.0)
        
        # Special case: detect "aif" when mentioned with "statements" or "reports"
        if ('aif' in text_lower and any(word in text_lower for word in ['statement', 'statements', 'report', 'reports', 'soa'])):
            aif_score = max(aif_score, 90.0)
        
        if aif_score > 0:
            aif_statements.append("AIF_Statement")
            max_confidence = max(max_confidence, aif_score)
        
        # Enhanced "all" patterns with higher confidence
        if any(pattern in text_lower for pattern in self.statement_keywords["all_patterns"]["all_statements"]):
            pms_statements = list(self.statement_keywords["pms"].keys())
            # Keep existing AIF if already detected
            if not aif_statements:
                aif_statements = ["AIF_Statement"]
            return pms_statements, aif_statements, 98.0
        
        if any(pattern in text_lower for pattern in self.statement_keywords["all_patterns"]["all_pms"]):
            pms_statements = list(self.statement_keywords["pms"].keys())
            return pms_statements, aif_statements, 97.0
        
        if any(pattern in text_lower for pattern in self.statement_keywords["all_patterns"]["all_aif"]):
            if not aif_statements:
                aif_statements = ["AIF_Statement"]
            return pms_statements, aif_statements, 97.0
        
        # Enhanced PMS keyword matching with context awareness
        for stmt_type, keywords in self.statement_keywords["pms"].items():
            stmt_score = 0
            exact_matches = 0
            
            # Primary keywords with exact and fuzzy matching
            for keyword in keywords["primary"]:
                if keyword in text_lower:
                    exact_matches += 1
                    stmt_score = max(stmt_score, 95.0 * keywords["weight"])
                else:
                    score = fuzz.partial_ratio(text_lower, keyword.lower())
                    if score >= 80:
                        stmt_score = max(stmt_score, score * keywords["weight"])
            
            # Secondary keywords with enhanced scoring
            for keyword in keywords["secondary"]:
                if keyword in text_lower:
                    stmt_score = max(stmt_score, 85.0 * keywords["weight"])
                else:
                    score = fuzz.partial_ratio(text_lower, keyword.lower())
                    if score >= 75:
                        stmt_score = max(stmt_score, score * keywords["weight"] * 0.85)
            
            # Boost confidence for exact matches
            if exact_matches > 0:
                stmt_score *= 1.1
            
            # Lower threshold for Portfolio_Appraisal when 'soa' is present
            threshold = 60
            if stmt_type == "Portfolio_Appraisal" and "soa" in text_lower:
                threshold = 50  # Lower threshold for SOA
            
            if stmt_score >= threshold:
                pms_statements.append(stmt_type)
                max_confidence = max(max_confidence, min(98.0, stmt_score))
        
        return pms_statements, aif_statements, max_confidence

    def extract_date_range(self, text: str) -> Tuple[Optional[datetime], Optional[datetime], float]:
        """Production-ready comprehensive date extraction covering all business scenarios"""
        dates = []
        text_lower = text.lower()
        now = datetime.now()
        
        # Step 1: Enhanced date finding with multiple methods
        try:
            found_dates = list(datefinder.find_dates(text))
            dates.extend([d for d in found_dates if 1990 <= d.year <= 2050])
        except:
            pass
        
        # Step 2: Comprehensive date patterns for all business scenarios
        additional_patterns = [
            # Standard date formats
            r'\b(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})\b',  # DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY
            r'\b(\d{2,4})[-/.](\d{1,2})[-/.](\d{1,2})\b',  # YYYY/MM/DD, YYYY-MM-DD, YYYY.MM.DD
            r'\b(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{2,4})\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2}),?\s+(\d{2,4})\b',
            r'\b(\d{1,2})(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{2,4})\b',
            r'\b(\d{2,4})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})\b',
            # Relative dates
            r'\b(today|yesterday|tomorrow)\b',
            # Month-Year formats
            r'\b(\d{1,2})[-/](\d{2,4})\b',  # MM/YYYY or MM-YYYY
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*[-\s]+(\d{2,4})\b',  # Month-Year
            # Quarter formats
            r'\bq[1-4]\s+(\d{2,4})\b',  # Q1 2024
            r'\b(\d{1})(?:st|nd|rd|th)?\s+quarter\s+(\d{2,4})\b',  # 1st quarter 2024
            # Week formats
            r'\bweek\s+(\d{1,2})\s+(\d{2,4})\b',  # week 15 2024
            # Indian date formats
            r'\b(\d{1,2})[-/](\d{1,2})[-/](\d{2})\b',  # DD/MM/YY
            # End of month/quarter/year
            r'\bend\s+of\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{2,4})\b',
            r'\beom\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{2,4})\b',
            r'\beoq\s+q[1-4]\s+(\d{2,4})\b',  # End of quarter
            r'\beoy\s+(\d{2,4})\b'  # End of year
        ]
        
        for pattern in additional_patterns:
            matches = re.finditer(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                try:
                    date_str = match.group(0)
                    # Handle special cases
                    if date_str.lower() == 'today':
                        dates.append(datetime.now())
                    elif date_str.lower() == 'yesterday':
                        dates.append(datetime.now() - timedelta(days=1))
                    elif date_str.lower() == 'tomorrow':
                        dates.append(datetime.now() + timedelta(days=1))
                    else:
                        parsed_date = self.parse_flexible_date(date_str)
                        if parsed_date and 1990 <= parsed_date.year <= 2050:
                            dates.append(parsed_date)
                except:
                    continue
        
        # Comprehensive Financial Year and Period parsing
        now = datetime.now()
        current_year = now.year
        
        # Enhanced Financial Year patterns
        fy_patterns = {
            r'\b(current|this)\s+fy\b': lambda: self._get_current_fy(now),
            r'\b(current|this)\s+financial\s+year\b': lambda: self._get_current_fy(now),
            r'\b(last|previous)\s+fy\b': lambda: self._get_last_fy(now),
            r'\b(last|previous)\s+financial\s+year\b': lambda: self._get_last_fy(now),
            r'\bnext\s+fy\b': lambda: self._get_next_fy(now),
            r'\bfy\s*(\d{2})[-\s]*(\d{2})\b': lambda: self._get_fy_range(re.search(r'\bfy\s*(\d{2})[-\s]*(\d{2})\b', text_lower)),
            r'\bfy\s*(\d{4})[-\s]*(\d{2,4})\b': lambda: self._get_fy_range(re.search(r'\bfy\s*(\d{4})[-\s]*(\d{2,4})\b', text_lower)),
            r'\bfy\s*(\d{2,4})\b': lambda: self._get_specific_fy(re.search(r'\bfy\s*(\d{2,4})\b', text_lower).group(1)),
            r'\bfinancial\s+year\s*(\d{2})[-\s]*(\d{2})\b': lambda: self._get_fy_range(re.search(r'\bfinancial\s+year\s*(\d{2})[-\s]*(\d{2})\b', text_lower)),
            r'\bfinancial\s+year\s*(\d{4})[-\s]*(\d{2,4})\b': lambda: self._get_fy_range(re.search(r'\bfinancial\s+year\s*(\d{4})[-\s]*(\d{2,4})\b', text_lower))
        }
        
        # Comprehensive time period patterns with enhanced coverage
        period_patterns = {
            # Current periods
            r'\b(current|this)\s+(year|month|quarter)\b': lambda: self._get_current_period(re.search(r'\b(current|this)\s+(year|month|quarter)\b', text_lower).group(2), now),
            r'\b(last|previous)\s+(year|month|quarter)\b': lambda: self._get_last_period(re.search(r'\b(last|previous)\s+(year|month|quarter)\b', text_lower).group(2), now),
            
            # To-date patterns
            r'\bytd\b|\byear\s+to\s+date\b': lambda: (datetime(current_year, 1, 1).date(), now.date()),
            r'\bmtd\b|\bmonth\s+to\s+date\b': lambda: (now.replace(day=1).date(), now.date()),
            r'\bqtd\b|\bquarter\s+to\s+date\b': lambda: self._get_qtd(now),
            r'\bwtd\b|\bweek\s+to\s+date\b': lambda: self._get_wtd(now),
            
            # Specific day references
            r'\byesterday\b': lambda: ((now - timedelta(days=1)).date(), (now - timedelta(days=1)).date()),
            r'\btoday\b': lambda: (now.date(), now.date()),
            r'\btomorrow\b': lambda: ((now + timedelta(days=1)).date(), (now + timedelta(days=1)).date()),
            
            # Last N periods
            r'\blast\s+(\d+)\s+(days?|months?|years?|weeks?)\b': lambda: self._get_last_n_period(text_lower, now),
            r'\bpast\s+(\d+)\s+(days?|months?|years?|weeks?)\b': lambda: self._get_last_n_period(text_lower, now),
            r'\bprevious\s+(\d+)\s+(days?|months?|years?|weeks?)\b': lambda: self._get_last_n_period(text_lower, now),
            
            # Week patterns
            r'\blast\s+(week|fortnight)\b': lambda: self._get_last_week_period(text_lower, now),
            r'\bthis\s+(week|month|year)\b': lambda: self._get_this_period(text_lower, now),
            r'\bcurrent\s+(week|month|year)\b': lambda: self._get_this_period(text_lower, now),
            
            # Quarter patterns
            r'\bq[1-4]\s+(\d{2,4})\b': lambda: self._get_quarter_period(text_lower, now),
            r'\b(\d{1})(?:st|nd|rd|th)?\s+quarter\s+(\d{2,4})\b': lambda: self._get_quarter_period(text_lower, now),
            r'\blast\s+quarter\b': lambda: self._get_last_quarter(now),
            r'\bthis\s+quarter\b': lambda: self._get_current_quarter(now),
            r'\bcurrent\s+quarter\b': lambda: self._get_current_quarter(now),
            
            # Half-year patterns
            r'\bh[1-2]\s+(\d{2,4})\b': lambda: self._get_half_year_period(text_lower, now),
            r'\b(first|second)\s+half\s+(\d{2,4})\b': lambda: self._get_half_year_period(text_lower, now),
            
            # End of period patterns
            r'\bend\s+of\s+(month|quarter|year)\b': lambda: self._get_end_of_period(text_lower, now),
            r'\beom\b': lambda: self._get_end_of_month(now),
            r'\beoq\b': lambda: self._get_end_of_quarter(now),
            r'\beoy\b': lambda: self._get_end_of_year(now)
        }
        
        # Step 3: Check exact patterns first with enhanced error handling
        for pattern, handler in {**fy_patterns, **period_patterns}.items():
            if re.search(pattern, text.lower()):
                try:
                    result = handler()
                    if result and len(result) == 2:
                        return result[0], result[1], 95.0
                except Exception as e:
                    logger.debug(f"Pattern {pattern} failed: {e}")
                    continue
        
        # Dynamic fuzzy matching for ANY spelling mistakes
        target_keywords = ['current', 'previous', 'last', 'this', 'next', 'year', 'month', 'quarter', 'fy']
        text_words = text.lower().split()
        corrected_text = text.lower()
        
        for word in text_words:
            if len(word) >= 3:  # Only check words with 3+ characters
                best_match = None
                best_score = 0
                
                for keyword in target_keywords:
                    score = fuzz.ratio(word, keyword)
                    if score >= 75 and score > best_score:  # 75% similarity threshold
                        best_match = keyword
                        best_score = score
                
                if best_match and best_match != word:
                    corrected_text = corrected_text.replace(word, best_match)
        
        # Re-check patterns with corrected text
        if corrected_text != text.lower():
            for pattern, handler in {**fy_patterns, **period_patterns}.items():
                if re.search(pattern, corrected_text):
                    try:
                        result = handler()
                        if result:
                            confidence = 90.0 if best_score >= 85 else 85.0  # Confidence based on match quality
                            return result[0], result[1], confidence
                    except:
                        continue
        
        # Enhanced "from" pattern with proper date extraction
        from_patterns = [
            r'from\s+([^\s]+(?:\s+[^\s]+){0,3})(?:\s+to\s+|\s+for\s+|\s+PAN\s+|\s+DI\s+|$)',
            r'since\s+([^\s]+(?:\s+[^\s]+){0,3})(?:\s+to\s+|\s+for\s+|\s+PAN\s+|\s+DI\s+|$)'
        ]
        
        for pattern in from_patterns:
            from_match = re.search(pattern, text_lower)
            if from_match:
                from_date_str = from_match.group(1).strip()
                from_date = self.parse_flexible_date(from_date_str)
                if from_date:
                    # Check if there's a 'to' in the text after 'from'
                    has_to_pattern = re.search(r'from\s+[^\s]+.*?\s+to\s+', text_lower)
                    if has_to_pattern:
                        # There's a 'to' pattern, let range detection handle it
                        continue
                    else:
                        # No 'to' pattern, default to yesterday
                        yesterday = (datetime.today() - timedelta(days=1)).date()
                        return from_date.date(), yesterday, 95.0
        
        # Enhanced range detection with "to" patterns
        range_patterns = [
            r'from\s+([^\s]+(?:\s+[^\s]+){0,3})\s+to\s+([^\s]+(?:\s+[^\s]+){0,3})',
            r'between\s+([^\s]+(?:\s+[^\s]+){0,3})\s+(?:and|to)\s+([^\s]+(?:\s+[^\s]+){0,3})',
            r'([^\s]+(?:\s+[^\s]+){0,3})\s+to\s+([^\s]+(?:\s+[^\s]+){0,3})',
            r'period\s+from\s+([^\s]+(?:\s+[^\s]+){0,3})\s+to\s+([^\s]+(?:\s+[^\s]+){0,3})'
        ]
        
        for pattern in range_patterns:
            range_match = re.search(pattern, text_lower)
            if range_match:
                start_str = range_match.group(1).strip()
                end_str = range_match.group(2).strip()
                start_date = self.parse_flexible_date(start_str)
                end_date = self.parse_flexible_date(end_str)
                if start_date and end_date:
                    from_dt, to_dt = self._validate_date_range(start_date.date(), end_date.date())
                    return from_dt, to_dt, 98.0
        
        # Check for date ranges from found dates
        if len(dates) >= 2:
            dates.sort()
            from_dt, to_dt = self._validate_date_range(dates[0].date(), dates[-1].date())
            return from_dt, to_dt, 95.0
        elif len(dates) == 1:
            # Single date found - check if it's a 'from' context or 'as on' context
            single_date = dates[0].date()
            
            # Check for 'from' context more specifically
            from_context_patterns = [r'from\s+[^\s]*march', r'from\s+\d+\s+march', r'from\s+march\s+\d+', r'since\s+']
            is_from_context = any(re.search(pattern, text_lower) for pattern in from_context_patterns)
            
            if is_from_context or 'from' in text_lower:
                # From date context - to_date should be yesterday
                yesterday = (datetime.today() - timedelta(days=1)).date()
                return single_date, yesterday, 90.0
            else:
                # As on date context - from_date should be default
                return self.DEFAULT_FROM_DATE, single_date, 90.0
        
        return self.DEFAULT_FROM_DATE, (datetime.today() - timedelta(days=1)).date(), 0.0
    
    def _validate_date_range(self, from_date, to_date):
        """Validate and fix date range logic"""
        if not from_date or not to_date:
            return from_date, to_date
        
        # If from_date is after to_date, try to fix year inference
        if from_date > to_date:
            # Common case: "from 21 march to 25 march2024" where first date gets wrong year
            if from_date.year != to_date.year:
                # Try adjusting from_date to same year as to_date
                adjusted_from = from_date.replace(year=to_date.year)
                if adjusted_from <= to_date:
                    return adjusted_from, to_date
                
                # Try adjusting to_date to same year as from_date
                adjusted_to = to_date.replace(year=from_date.year)
                if from_date <= adjusted_to:
                    return from_date, adjusted_to
        
        return from_date, to_date
    
    def _get_current_fy(self, now):
        if now.month >= 4:
            return datetime(now.year, 4, 1).date(), datetime(now.year + 1, 3, 31).date()
        else:
            return datetime(now.year - 1, 4, 1).date(), datetime(now.year, 3, 31).date()
    
    def _get_last_fy(self, now):
        if now.month >= 4:
            return datetime(now.year - 1, 4, 1).date(), datetime(now.year, 3, 31).date()
        else:
            return datetime(now.year - 2, 4, 1).date(), datetime(now.year - 1, 3, 31).date()
    
    def _get_next_fy(self, now):
        if now.month >= 4:
            return datetime(now.year + 1, 4, 1).date(), datetime(now.year + 2, 3, 31).date()
        else:
            return datetime(now.year, 4, 1).date(), datetime(now.year + 1, 3, 31).date()
    
    def _get_specific_fy(self, year_str):
        year = int(year_str)
        if year < 100:
            year = 2000 + year if year <= 50 else 1900 + year
        # For FY24, return FY24-25 (Apr 2024 to Mar 2025)
        return datetime(year, 4, 1).date(), datetime(year + 1, 3, 31).date()
    
    def _get_current_period(self, period, now):
        if period == 'year':
            return datetime(now.year, 1, 1).date(), now.date()
        elif period == 'month':
            return now.replace(day=1).date(), now.date()
        elif period == 'quarter':
            q = (now.month - 1) // 3 + 1
            start_month = (q - 1) * 3 + 1
            return datetime(now.year, start_month, 1).date(), now.date()
    
    def _get_last_period(self, period, now):
        if period == 'year':
            return datetime(now.year - 1, 1, 1).date(), datetime(now.year - 1, 12, 31).date()
        elif period == 'month':
            last_month = now.replace(day=1) - timedelta(days=1)
            return last_month.replace(day=1).date(), last_month.date()
        elif period == 'quarter':
            q = (now.month - 1) // 3 + 1
            if q == 1:
                return datetime(now.year - 1, 10, 1).date(), datetime(now.year - 1, 12, 31).date()
            else:
                start_month = (q - 2) * 3 + 1
                end_month = start_month + 2
                return datetime(now.year, start_month, 1).date(), datetime(now.year, end_month, 31).date()
    
    def _get_qtd(self, now):
        q = (now.month - 1) // 3 + 1
        start_month = (q - 1) * 3 + 1
        return datetime(now.year, start_month, 1).date(), now.date()
    
    def _get_last_n_period(self, text, now):
        patterns = [r'\b(?:last|past|previous)\s+(\d+)\s+(days?|months?|years?|weeks?)\b']
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                n = int(match.group(1))
                unit = match.group(2)
                if 'day' in unit:
                    start_date = now - timedelta(days=n)
                elif 'week' in unit:
                    start_date = now - timedelta(weeks=n)
                elif 'month' in unit:
                    start_date = now - relativedelta(months=n)
                elif 'year' in unit:
                    start_date = now - relativedelta(years=n)
                return start_date.date(), now.date()
        return None
    
    def _get_wtd(self, now):
        """Week to date - Monday to today"""
        days_since_monday = now.weekday()
        start_date = now - timedelta(days=days_since_monday)
        return start_date.date(), now.date()
    
    def _get_quarter_period(self, text, now):
        """Get specific quarter period"""
        # Extract quarter and year from text
        q_match = re.search(r'\bq([1-4])\s+(\d{2,4})\b', text)
        if not q_match:
            q_match = re.search(r'\b([1-4])(?:st|nd|rd|th)?\s+quarter\s+(\d{2,4})\b', text)
        
        if q_match:
            quarter = int(q_match.group(1))
            year = int(q_match.group(2))
            if year < 100:
                year = 2000 + year if year <= 50 else 1900 + year
            
            start_month = (quarter - 1) * 3 + 1
            end_month = start_month + 2
            
            # Get last day of end month
            if end_month == 12:
                end_date = datetime(year, 12, 31).date()
            else:
                end_date = (datetime(year, end_month + 1, 1) - timedelta(days=1)).date()
            
            return datetime(year, start_month, 1).date(), end_date
        return None
    
    def _get_last_quarter(self, now):
        """Get last quarter dates"""
        current_quarter = (now.month - 1) // 3 + 1
        if current_quarter == 1:
            # Last quarter is Q4 of previous year
            return datetime(now.year - 1, 10, 1).date(), datetime(now.year - 1, 12, 31).date()
        else:
            start_month = (current_quarter - 2) * 3 + 1
            end_month = start_month + 2
            end_date = (datetime(now.year, end_month + 1, 1) - timedelta(days=1)).date()
            return datetime(now.year, start_month, 1).date(), end_date
    
    def _get_current_quarter(self, now):
        """Get current quarter dates"""
        current_quarter = (now.month - 1) // 3 + 1
        start_month = (current_quarter - 1) * 3 + 1
        return datetime(now.year, start_month, 1).date(), now.date()
    
    def _get_half_year_period(self, text, now):
        """Get half-year period"""
        h_match = re.search(r'\bh([1-2])\s+(\d{2,4})\b', text)
        if not h_match:
            h_match = re.search(r'\b(first|second)\s+half\s+(\d{2,4})\b', text)
            if h_match:
                half = 1 if h_match.group(1) == 'first' else 2
                year = int(h_match.group(2))
            else:
                return None
        else:
            half = int(h_match.group(1))
            year = int(h_match.group(2))
        
        if year < 100:
            year = 2000 + year if year <= 50 else 1900 + year
        
        if half == 1:
            return datetime(year, 1, 1).date(), datetime(year, 6, 30).date()
        else:
            return datetime(year, 7, 1).date(), datetime(year, 12, 31).date()
    
    def _get_end_of_period(self, text, now):
        """Get end of specified period"""
        if 'month' in text:
            return self._get_end_of_month(now)
        elif 'quarter' in text:
            return self._get_end_of_quarter(now)
        elif 'year' in text:
            return self._get_end_of_year(now)
        return None
    
    def _get_end_of_month(self, now):
        """Get end of current month"""
        if now.month == 12:
            end_date = datetime(now.year, 12, 31).date()
        else:
            end_date = (datetime(now.year, now.month + 1, 1) - timedelta(days=1)).date()
        return self.DEFAULT_FROM_DATE, end_date
    
    def _get_end_of_quarter(self, now):
        """Get end of current quarter"""
        current_quarter = (now.month - 1) // 3 + 1
        end_month = current_quarter * 3
        if end_month == 12:
            end_date = datetime(now.year, 12, 31).date()
        else:
            end_date = (datetime(now.year, end_month + 1, 1) - timedelta(days=1)).date()
        return self.DEFAULT_FROM_DATE, end_date
    
    def _get_end_of_year(self, now):
        """Get end of current year"""
        return self.DEFAULT_FROM_DATE, datetime(now.year, 12, 31).date()
    
    def _get_last_week_period(self, text, now):
        if 'week' in text:
            # Last week: Monday to Sunday of previous week
            days_since_monday = now.weekday()
            this_monday = now - timedelta(days=days_since_monday)
            last_monday = this_monday - timedelta(weeks=1)
            last_sunday = last_monday + timedelta(days=6)
            return last_monday.date(), last_sunday.date()
        elif 'fortnight' in text:
            start_date = now - timedelta(weeks=2)
            return start_date.date(), now.date()
        return None
    
    def _get_this_period(self, text, now):
        if 'week' in text:
            # Start of current week (Monday)
            days_since_monday = now.weekday()
            start_date = now - timedelta(days=days_since_monday)
            return start_date.date(), now.date()
        elif 'month' in text:
            return now.replace(day=1).date(), now.date()
        elif 'year' in text:
            return datetime(now.year, 1, 1).date(), now.date()
        return None
    
    def _get_fy_range(self, match):
        if not match:
            return None
        
        year1_str = match.group(1)
        year2_str = match.group(2) if match.lastindex >= 2 else None
        
        year1 = int(year1_str)
        if year2_str:
            year2 = int(year2_str)
            # Handle 2-digit years
            if year1 < 100:
                year1 = 2000 + year1 if year1 <= 50 else 1900 + year1
            if year2 < 100:
                year2 = 2000 + year2 if year2 <= 50 else 1900 + year2
            # For FY23-24, return Apr 2023 to Mar 2024
            return datetime(year1, 4, 1).date(), datetime(year2, 3, 31).date()
        else:
            # Single year FY
            return self._get_specific_fy(year1_str)

    def parse_flexible_date(self, date_str: str) -> Optional[datetime]:
        """Advanced date parser using multiple methods"""
        if not date_str:
            return None
        
        # Method 1: datefinder
        try:
            dates = list(datefinder.find_dates(date_str))
            if dates and 1990 <= dates[0].year <= 2050:
                return dates[0]
        except:
            pass
        
        # Method 2: dateparser with multiple settings
        settings_list = [
            {'DATE_ORDER': 'DMY', 'STRICT_PARSING': False},
            {'DATE_ORDER': 'MDY', 'STRICT_PARSING': False},
            {'DATE_ORDER': 'YMD', 'STRICT_PARSING': False},
            {'PREFER_DAY_OF_MONTH': 'first'},
            {}
        ]
        
        for settings in settings_list:
            try:
                parsed = dateparser.parse(date_str, settings=settings)
                if parsed and 1990 <= parsed.year <= 2050:
                    return parsed
            except:
                continue
        
        return None

    def calculate_confidence(self, stmt_confidence: float, date_confidence: float, 
                           has_identifiers: bool, identifiers: Dict) -> float:
        """Enhanced confidence calculation with multi-factor scoring"""
        weights = self.model_config["confidence_weights"]
        
        # Enhanced identifier scoring
        identifier_score = 0
        if identifiers["pan_numbers"]:
            identifier_score += 40
        if identifiers["di_code"]:
            identifier_score += 35
        if identifiers["aif_folio"]:
            identifier_score += 15
        if identifiers["account_code"]:
            identifier_score += 10
        
        identifier_confidence = min(100.0, identifier_score) if has_identifiers else 30.0
        
        # Boost confidence for high-quality combinations
        base_confidence = (
            stmt_confidence * weights["statement_type"] +
            date_confidence * weights["date_parsing"] +
            identifier_confidence * weights["identifiers"]
        )
        
        # Apply confidence boosters
        if stmt_confidence >= 90 and has_identifiers:
            base_confidence *= 1.05
        if date_confidence >= 90 and stmt_confidence >= 85:
            base_confidence *= 1.03
        if len(identifiers["pan_numbers"]) > 0 and len(identifiers["di_code"]) > 0:
            base_confidence *= 1.02
        
        return min(100.0, base_confidence)

    def parse_email(self, text: str) -> Dict[str, Any]:
        """Main parsing function with ML fallback"""
        # Extract identifiers
        identifiers = self.extract_identifiers(text)
        
        # Rule-based parsing
        pms_statements, aif_statements, stmt_confidence = self.match_statement_types(text)
        from_date, to_date, date_confidence = self.extract_date_range(text)
        
        has_identifiers = any(identifiers.values())
        overall_confidence = self.calculate_confidence(stmt_confidence, date_confidence, has_identifiers, identifiers)
        
        parsing_method = "rule_based"
        
        # Business logic validation and statement category determination
        statement_category = []
        all_statements = []
        
        # ML Enhancement if confidence is below threshold (enhance, don't replace)
        ml_threshold = self.model_config.get("ml_fallback_threshold", 60.0)
        if overall_confidence < ml_threshold and self.ml_model is not None:
            logger.info(f"Rule-based confidence {overall_confidence:.2f} < {ml_threshold}, enhancing with ML")
            ml_result = self._ml_fallback_parse(text, identifiers)
            if ml_result:
                # Enhance rule-based results with ML predictions
                ml_pms = ml_result.get("pms_statements", [])
                ml_aif = ml_result.get("aif_statements", [])
                ml_confidence = ml_result.get("confidence", 0)
                
                # Add ML predictions to existing rule-based results
                for stmt in ml_pms:
                    if stmt not in pms_statements:
                        pms_statements.append(stmt)
                        logger.info(f"ML enhanced: Added PMS statement {stmt}")
                
                for stmt in ml_aif:
                    if stmt not in aif_statements:
                        aif_statements.append(stmt)
                        logger.info(f"ML enhanced: Added AIF statement {stmt}")
                
                # Use better date range if ML found one
                ml_from_date = ml_result.get("from_date")
                ml_to_date = ml_result.get("to_date")
                if ml_from_date and ml_to_date and date_confidence < 50:
                    from_date = ml_from_date
                    to_date = ml_to_date
                    logger.info("ML enhanced: Improved date range")
                
                # Boost confidence if ML added value
                if ml_pms or ml_aif or (ml_from_date and date_confidence < 50):
                    confidence_boost = min(15.0, ml_confidence * 0.2)
                    overall_confidence = min(95.0, overall_confidence + confidence_boost)
                    parsing_method = "rule_based_ml_enhanced"
                    logger.info(f"ML enhanced confidence from {overall_confidence-confidence_boost:.2f} to {overall_confidence:.2f}")
        has_aif_folio = len(identifiers["aif_folio"]) > 0
        has_pan = len(identifiers["pan_numbers"]) > 0
        has_di = len(identifiers["di_code"]) > 0
        
        # Priority 1: User keywords (PMS statements)
        if pms_statements:
            statement_category.append("PMS")
            all_statements.extend(pms_statements)
            logger.info(f"PMS statements detected from keywords: {pms_statements}")
        
        # Priority 2: User keywords (AIF statements) - allow if identifiers present OR explicitly mentioned
        if aif_statements:
            has_only_di = has_di and not has_pan and not has_aif_folio
            no_identifiers = not has_pan and not has_di and not has_aif_folio
            
            if has_aif_folio or has_pan or no_identifiers:
                if "AIF" not in statement_category:
                    statement_category.append("AIF")
                for stmt in aif_statements:
                    if stmt not in all_statements:
                        all_statements.append(stmt)
                logger.info(f"AIF statements detected from keywords: {aif_statements}")
            elif has_only_di:
                logger.warning("AIF statements require AIF folio or PAN, not DI code only")
                overall_confidence = min(100.0, overall_confidence * 1.1)
        
        # Priority 3: Auto-add AIF statement ONLY if AIF folio is present AND no AIF keywords were found
        if has_aif_folio and not aif_statements:
            if "AIF" not in statement_category:
                statement_category.append("AIF")
            if "AIF_Statement" not in all_statements:
                all_statements.append("AIF_Statement")
            logger.info("AIF folio detected without AIF keywords - adding AIF_Statement")
        
        # Final validation - ensure we have at least one statement type
        if len(all_statements) == 0:
            # Default fallback based on identifiers
            if has_aif_folio:
                statement_category = ["AIF"]
                all_statements = ["AIF_Statement"]
            elif has_pan or has_di:
                statement_category = ["PMS"]
                all_statements = ["Portfolio_Appraisal"]
            logger.info(f"Applied default fallback: {all_statements}")
        
        return {
            "statement_category": statement_category,
            "statement_types": all_statements,
            "aif_folio": identifiers["aif_folio"],
            "di_code": identifiers["di_code"],
            "account_code": identifiers["account_code"],
            "pan_numbers": identifiers["pan_numbers"],
            "from_date": str(from_date) if from_date else None,
            "to_date": str(to_date) if to_date else None,
            "confidence": round(overall_confidence, 2),
            "metadata": {
                "date_source": "email" if date_confidence > 0 else "default",
                "parsing_method": parsing_method,
                "model_version": self.model_config["version"],
                "has_identifiers": has_identifiers,
                "business_logic_applied": True,
                "ml_fallback_used": parsing_method in ["ml_fallback", "rule_based_ml_enhanced"],
                "ml_enhanced": parsing_method == "rule_based_ml_enhanced"
            },
            "raw_text": text
        }
    
    def _ml_fallback_parse(self, text: str, identifiers: Dict) -> Optional[Dict]:
        """Production-ready ML fallback parsing when rule-based confidence is low"""
        if not self.ml_model or not self.vectorizer:
            logger.debug("ML model or vectorizer not available")
            return None
        
        try:
            # Enhanced feature extraction
            features = self._extract_ml_features(text, identifiers)
            X = self.vectorizer.transform([features])
            
            # Get predictions and probabilities
            predictions = self.ml_model.predict(X)[0]
            probabilities = self.ml_model.predict_proba(X)
            
            # Parse predictions with enhanced logic
            pms_statements = self._decode_statement_predictions(predictions[:10])  # First 10 for PMS
            aif_statements = self._decode_aif_predictions(predictions[10:11])     # Next 1 for AIF
            
            # Enhanced date prediction using rule-based as fallback
            from_date, to_date = self._predict_dates_ml(text)
            
            # Calculate ML confidence with multiple factors
            ml_confidence = self._calculate_ml_confidence(probabilities, predictions, identifiers)
            
            # Apply business logic validation
            pms_statements, aif_statements = self._validate_ml_predictions(
                pms_statements, aif_statements, identifiers
            )
            
            logger.info(f"ML fallback: PMS={pms_statements}, AIF={aif_statements}, confidence={ml_confidence:.2f}")
            
            return {
                "pms_statements": pms_statements,
                "aif_statements": aif_statements,
                "from_date": from_date,
                "to_date": to_date,
                "confidence": ml_confidence
            }
        except Exception as e:
            logger.error(f"ML fallback failed: {e}")
            return None
    
    def _extract_ml_features(self, text: str, identifiers: Dict) -> str:
        """Enhanced feature extraction for ML model with comprehensive text analysis"""
        features = []
        text_lower = text.lower()
        
        # Core text features
        features.append(text_lower)
        
        # Identifier features with counts
        pan_count = len(identifiers.get("pan_numbers", []))
        di_count = len(identifiers.get("di_code", []))
        aif_count = len(identifiers.get("aif_folio", []))
        account_count = len(identifiers.get("account_code", []))
        
        if pan_count > 0:
            features.append(f"has_pan_{min(pan_count, 3)}")  # Cap at 3 for feature stability
        if di_count > 0:
            features.append(f"has_di_code_{min(di_count, 3)}")
        if aif_count > 0:
            features.append(f"has_aif_folio_{min(aif_count, 3)}")
        if account_count > 0:
            features.append(f"has_account_code_{min(account_count, 3)}")
        
        # Text pattern features
        if any(word in text_lower for word in ['send', 'please', 'provide', 'share']):
            features.append("has_request_words")
        if any(word in text_lower for word in ['statement', 'report', 'soa']):
            features.append("has_statement_words")
        if any(word in text_lower for word in ['as on', 'from', 'to', 'between']):
            features.append("has_date_words")
        if any(word in text_lower for word in ['all', 'complete', 'entire']):
            features.append("has_all_words")
        
        # Length features
        word_count = len(text.split())
        if word_count <= 10:
            features.append("short_text")
        elif word_count <= 20:
            features.append("medium_text")
        else:
            features.append("long_text")
        
        # spaCy features with enhanced entity extraction
        if self.nlp:
            try:
                doc = self.nlp(text)
                entity_counts = {}
                
                for ent in doc.ents:
                    if ent.label_ in ["DATE", "MONEY", "ORG", "PERSON", "GPE", "CARDINAL"]:
                        entity_counts[ent.label_] = entity_counts.get(ent.label_, 0) + 1
                
                for label, count in entity_counts.items():
                    features.append(f"entity_{label.lower()}_{min(count, 3)}")
                
                # POS tag features for key words
                for token in doc:
                    if token.text.lower() in ['statement', 'report', 'send', 'provide']:
                        features.append(f"pos_{token.pos_.lower()}")
                        
            except Exception as e:
                logger.debug(f"spaCy processing failed: {e}")
        
        return " ".join(features)
    
    def _decode_statement_predictions(self, predictions) -> List[str]:
        """Decode PMS statement predictions with confidence thresholding"""
        pms_types = list(self.statement_keywords["pms"].keys())
        threshold = 0.3  # Lower threshold for ML fallback
        return [pms_types[i] for i, pred in enumerate(predictions) if pred > threshold and i < len(pms_types)]
    
    def _decode_aif_predictions(self, predictions) -> List[str]:
        """Decode AIF statement predictions with confidence thresholding"""
        threshold = 0.3  # Lower threshold for ML fallback
        return ["AIF_Statement"] if predictions[0] > threshold else []
    
    def _predict_dates_ml(self, text: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """Enhanced date prediction for ML fallback using rule-based extraction"""
        # Use existing comprehensive date extraction
        from_date, to_date, confidence = self.extract_date_range(text)
        
        # If no dates found, provide sensible defaults
        if not from_date or not to_date:
            from_date = self.DEFAULT_FROM_DATE
            to_date = (datetime.now() - timedelta(days=1)).date()
        
        return from_date, to_date
    
    def _calculate_ml_confidence(self, probabilities, predictions, identifiers) -> float:
        """Calculate ML confidence with multiple factors"""
        try:
            # Base confidence from model probabilities
            if len(probabilities) > 0 and len(probabilities[0]) > 0:
                base_confidence = np.mean([np.max(prob) for prob in probabilities]) * 100
            else:
                base_confidence = 50.0
            
            # Boost confidence based on identifiers
            identifier_boost = 0
            if identifiers.get("pan_numbers"):
                identifier_boost += 10
            if identifiers.get("di_code"):
                identifier_boost += 8
            if identifiers.get("aif_folio"):
                identifier_boost += 5
            if identifiers.get("account_code"):
                identifier_boost += 3
            
            # Boost confidence based on prediction strength
            prediction_boost = 0
            active_predictions = sum(1 for pred in predictions if pred > 0.3)
            if active_predictions == 1:  # Single clear prediction
                prediction_boost += 5
            elif active_predictions > 3:  # Too many predictions, reduce confidence
                prediction_boost -= 10
            
            final_confidence = min(95.0, base_confidence + identifier_boost + prediction_boost)
            return max(30.0, final_confidence)  # Minimum 30% confidence
            
        except Exception as e:
            logger.error(f"ML confidence calculation failed: {e}")
            return 50.0
    
    def _validate_ml_predictions(self, pms_statements, aif_statements, identifiers) -> Tuple[List[str], List[str]]:
        """Apply business logic validation to ML predictions"""
        # AIF statements require AIF folio or PAN (not DI code only)
        if aif_statements:
            has_aif_folio = len(identifiers.get("aif_folio", [])) > 0
            has_pan = len(identifiers.get("pan_numbers", [])) > 0
            has_only_di = len(identifiers.get("di_code", [])) > 0 and not has_pan and not has_aif_folio
            
            if has_only_di:
                logger.info("ML: Filtering out AIF statements - only DI code provided")
                aif_statements = []
        
        # If no statements predicted, default to Portfolio_Appraisal for PMS
        if not pms_statements and not aif_statements:
            if any(identifiers.values()):
                pms_statements = ["Portfolio_Appraisal"]
                logger.info("ML: Defaulting to Portfolio_Appraisal")
        
        return pms_statements, aif_statements
    
    def generate_training_data(self, size: int = 1000) -> List[Dict]:
        """Generate comprehensive synthetic training data covering all business scenarios"""
        training_data = []
        
        # Enhanced statement type templates with more variety
        pms_templates = [
            # Basic requests
            "Please send me {statement} for PAN {pan} as on {date}",
            "I need {statement} for DI {di_code} from {from_date} to {to_date}",
            "Send {statement} for account {account} as on {date}",
            "Please provide {statement} for {date}",
            "I require {statement} for PAN {pan}",
            "Can you send me {statement} for the period {from_date} to {to_date}",
            "Please share {statement} as on {date} for DI {di_code}",
            "I need latest {statement} for PAN {pan} and DI {di_code}",
            
            # Formal requests
            "Kindly provide {statement} for PAN {pan} as on {date}",
            "Request for {statement} for DI {di_code} for the period {from_date} to {to_date}",
            "Please forward {statement} for account {account} as on {date}",
            "I would like to receive {statement} for {date}",
            "Could you please send {statement} for PAN {pan}?",
            
            # Urgent requests
            "Urgent: Need {statement} for PAN {pan} as on {date}",
            "ASAP - {statement} required for DI {di_code}",
            "Priority request for {statement} as on {date}",
            
            # Multiple identifiers
            "Send {statement} for PAN {pan}, DI {di_code} as on {date}",
            "Please provide {statement} for PAN {pan} and account {account}",
            "I need {statement} for all accounts - PAN {pan}, DI {di_code}",
            
            # Period-specific requests
            "Please send {statement} for FY 23-24",
            "I need {statement} for last quarter",
            "Send {statement} for current financial year",
            "Please provide {statement} for YTD",
            "I require {statement} for last 6 months",
            "Send {statement} for Q1 2024",
            
            # All statements requests
            "Please send all statements for PAN {pan}",
            "I need complete PMS statements for DI {di_code}",
            "Send all reports for account {account}",
            "Please provide everything for PAN {pan} as on {date}"
        ]
        
        aif_templates = [
            # Basic AIF requests
            "Please send AIF statement for folio {aif_folio} as on {date}",
            "I need AIF report for PAN {pan} as on {date}",
            "Send AIF statement for {aif_folio} from {from_date} to {to_date}",
            "Please provide AIF factsheet for folio {aif_folio}",
            "I require AIF statement for PAN {pan} and folio {aif_folio}",
            
            # Formal AIF requests
            "Kindly provide AIF statement for folio {aif_folio}",
            "Request for AIF report for PAN {pan} as on {date}",
            "Please forward AIF statement for {aif_folio}",
            
            # Alternative Investment Fund variations
            "Send Alternative Investment Fund statement for {aif_folio}",
            "I need alternative investment fund report for PAN {pan}",
            "Please provide AIF portfolio statement for folio {aif_folio}",
            
            # Period-specific AIF requests
            "AIF statement required for FY 23-24 for folio {aif_folio}",
            "Please send AIF report for last quarter for PAN {pan}",
            "I need AIF statement for YTD for folio {aif_folio}"
        ]
        
        # Date format variations for more realistic training
        date_formats = [
            "%d-%b-%Y",    # 15-Mar-2024
            "%d/%m/%Y",    # 15/03/2024
            "%d.%m.%Y",    # 15.03.2024
            "%d %B %Y",    # 15 March 2024
            "%B %d, %Y",   # March 15, 2024
            "%d-%m-%Y",    # 15-03-2024
        ]
        
        # Period expressions for training
        period_expressions = [
            "FY 23-24", "FY 2023-24", "financial year 2023-24",
            "last quarter", "current quarter", "Q1 2024", "Q2 2024",
            "last 3 months", "last 6 months", "last year",
            "YTD", "year to date", "MTD", "month to date",
            "current financial year", "previous financial year",
            "this year", "last year", "current year",
            "yesterday", "today", "last week", "this month"
        ]
        
        # Generate comprehensive samples
        import random
        from datetime import date, timedelta
        
        # Ensure balanced representation of all statement types
        pms_keys = list(self.statement_keywords["pms"].keys())
        all_statement_types = pms_keys + ["AIF_Statement"]
        
        # Calculate minimum samples per statement type
        min_samples_per_type = max(10, size // (len(all_statement_types) * 2))  # At least 10 samples per type
        guaranteed_samples = {stmt_type: 0 for stmt_type in all_statement_types}
        
        for i in range(size):
            # First, ensure minimum representation for each statement type
            if i < len(all_statement_types) * min_samples_per_type:
                stmt_type = all_statement_types[i % len(all_statement_types)]
                guaranteed_samples[stmt_type] += 1
                
                if stmt_type == "AIF_Statement":
                    template = random.choice(aif_templates)
                    statement_category = ["AIF"]
                    statement_types = ["AIF_Statement"]
                else:
                    template = random.choice(pms_templates)
                    statement_category = ["PMS"]
                    statement_types = [stmt_type]
            else:
                # Then generate with normal distribution
                if random.random() < 0.75:  # 75% PMS, 25% AIF
                    template = random.choice(pms_templates)
                    statement_category = ["PMS"]
                    
                    # Sometimes generate multiple statement types for "all" requests
                    if "all" in template.lower() or "complete" in template.lower():
                        if random.random() < 0.3:  # 30% chance for multiple statements
                            statement_types = random.sample(pms_keys, random.randint(2, 4))
                        else:
                            statement_types = [random.choice(pms_keys)]
                    else:
                        statement_types = [random.choice(pms_keys)]
                else:
                    template = random.choice(aif_templates)
                    statement_category = ["AIF"]
                    statement_types = ["AIF_Statement"]
            
            # Generate realistic identifiers
            pan = self._generate_pan()
            di_code = self._generate_di_code()
            account = f"{random.randint(10000000, 99999999)}"
            aif_folio = f"{random.choice([5,6,7,8,9])}{random.randint(100000000, 999999999)}"
            
            # Generate varied date ranges
            base_date = date.today() - timedelta(days=random.randint(1, 730))  # Up to 2 years back
            from_date = base_date - timedelta(days=random.randint(30, 365))
            to_date = base_date
            
            # Choose date format randomly
            date_format = random.choice(date_formats)
            
            # Sometimes use period expressions instead of specific dates
            if random.random() < 0.3 and "{date}" in template:
                # Replace date with period expression
                period_expr = random.choice(period_expressions)
                template = template.replace("as on {date}", f"for {period_expr}")
                template = template.replace("for {date}", f"for {period_expr}")
                
                # Fill template without date
                text = template.format(
                    statement=statement_types[0].lower().replace("_", " "),
                    pan=pan,
                    di_code=di_code,
                    account=account,
                    aif_folio=aif_folio
                )
            else:
                # Fill template with formatted dates
                text = template.format(
                    statement=statement_types[0].lower().replace("_", " "),
                    pan=pan,
                    di_code=di_code,
                    account=account,
                    aif_folio=aif_folio,
                    date=base_date.strftime(date_format),
                    from_date=from_date.strftime(date_format),
                    to_date=to_date.strftime(date_format)
                )
            
            # Add some natural variations
            if random.random() < 0.1:  # 10% chance to add extra words
                variations = ["Thanks", "Regards", "Please confirm", "Urgent", "ASAP"]
                text += f" {random.choice(variations)}"
            
            # Add some typos occasionally for robustness
            if random.random() < 0.05:  # 5% chance for minor typos
                typos = {
                    "statement": "statment",
                    "please": "plz",
                    "provide": "provde",
                    "required": "requird"
                }
                for correct, typo in typos.items():
                    if correct in text.lower() and random.random() < 0.5:
                        text = text.replace(correct, typo)
                        break
            
            # Calculate realistic confidence based on content quality
            confidence = 85.0
            if any(id_list for id_list in [pan, di_code, account, aif_folio] if pan in text or di_code in text):
                confidence += 5  # Boost for identifiers
            if any(word in text.lower() for word in ['as on', 'from', 'to', 'period']):
                confidence += 3  # Boost for date words
            if len(statement_types) == 1:
                confidence += 2  # Boost for single clear statement type
            
            # Add some randomness
            confidence += random.uniform(-3, 5)
            confidence = min(98.0, max(80.0, confidence))
            
            training_data.append({
                "text": text,
                "labels": {
                    "statement_category": list(statement_category),  # Ensure it's a list
                    "statement_types": list(statement_types),        # Ensure it's a list
                    "from_date": str(from_date),
                    "to_date": str(to_date),
                    "confidence": confidence
                }
            })
        
        # Add some edge cases for robustness
        edge_cases = [
            {
                "text": "send all statements",
                "labels": {
                    "statement_category": ["PMS"],
                    "statement_types": list(self.statement_keywords["pms"].keys()),
                    "from_date": str(self.DEFAULT_FROM_DATE),
                    "to_date": str(date.today() - timedelta(days=1)),
                    "confidence": 75.0
                }
            },
            {
                "text": "pls send soa",
                "labels": {
                    "statement_category": ["PMS"],
                    "statement_types": ["Portfolio_Appraisal"],
                    "from_date": str(self.DEFAULT_FROM_DATE),
                    "to_date": str(date.today() - timedelta(days=1)),
                    "confidence": 80.0
                }
            },
            {
                "text": "AIF report needed",
                "labels": {
                    "statement_category": ["AIF"],
                    "statement_types": ["AIF_Statement"],
                    "from_date": str(self.DEFAULT_FROM_DATE),
                    "to_date": str(date.today() - timedelta(days=1)),
                    "confidence": 78.0
                }
            }
        ]
        
        training_data.extend(edge_cases)
        
        logger.info(f"Generated {len(training_data)} training samples with enhanced variety")
        # Log distribution of statement types
        type_counts = {}
        for sample in training_data:
            for stmt_type in sample["labels"]["statement_types"]:
                type_counts[stmt_type] = type_counts.get(stmt_type, 0) + 1
        
        logger.info(f"Generated {len(training_data)} training samples with enhanced variety")
        logger.info("Statement type distribution:")
        for stmt_type, count in sorted(type_counts.items()):
            logger.info(f"  {stmt_type:25}: {count:4d} samples ({count/len(training_data)*100:.1f}%)")
        
        # Add comprehensive human language patterns
        try:
            with open('training_data/human_language_training.json', 'r') as f:
                human_data = json.load(f)
                training_data.extend(human_data)
                logger.info(f"Added {len(human_data)} human language training samples")
        except FileNotFoundError:
            logger.warning("Human language training data not found, run generate_human_training_data.py first")
        
        # Add comprehensive date training patterns
        try:
            with open('training_data/date_training.json', 'r') as f:
                date_data = json.load(f)
                # Convert date training format to standard format
                for sample in date_data:
                    training_data.append({
                        "text": sample["text"],
                        "labels": {
                            "statement_category": ["PMS"],
                            "statement_types": ["Portfolio_Appraisal"],
                            "from_date": sample["from_date"],
                            "to_date": sample["to_date"],
                            "confidence": sample["confidence"]
                        }
                    })
                logger.info(f"Added {len(date_data)} date training samples")
        except FileNotFoundError:
            logger.warning("Date training data not found, run generate_date_training_data.py first")
        
        return training_data
    
    def _generate_pan(self) -> str:
        """Generate realistic PAN format following actual patterns"""
        import random
        import string
        
        # First 3 letters often follow patterns (company/person type)
        first_patterns = ['ABC', 'DEF', 'GHI', 'JKL', 'MNO', 'PQR', 'STU', 'VWX', 'YZA']
        first_three = random.choice(first_patterns)
        
        # Next 2 letters
        next_two = ''.join(random.choices(string.ascii_uppercase, k=2))
        
        # 4 digits
        digits = ''.join(random.choices(string.digits, k=4))
        
        # Last letter (check digit)
        last_letter = random.choice(string.ascii_uppercase)
        
        return f"{first_three}{next_two}{digits}{last_letter}"
    
    def _generate_di_code(self) -> str:
        """Generate realistic DI code format"""
        import random
        import string
        
        # DI codes can be D followed by 7 alphanumeric or DI followed by 6
        if random.random() < 0.7:  # 70% D + 7 chars
            code = 'D' + ''.join(random.choices(string.digits + string.ascii_uppercase, k=7))
        else:  # 30% DI + 6 chars
            code = 'DI' + ''.join(random.choices(string.digits + string.ascii_uppercase, k=6))
        
        return code