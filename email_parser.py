import re
import json
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fuzzywuzzy import fuzz
import dateparser
import datefinder
from typing import Dict, List, Tuple, Optional, Any


logger = logging.getLogger('IpruAI.Parser')

class IpruAIEmailParser:
    def __init__(self):
        self.load_configs()
        self.DEFAULT_FROM_DATE = datetime(1990, 1, 1).date()
        
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

    def extract_identifiers(self, text: str) -> Dict[str, List[str]]:
        """Extract PAN, DI codes, Account IDs, and AIF folios"""
        text_upper = text.upper()
        
        # Enhanced PAN extraction with context validation
        pan_pattern = self.regex_patterns["identifiers"]["pan"]
        pan_matches = re.findall(pan_pattern, text_upper)
        # Validate PAN format more strictly
        pans = list(set([pan for pan in pan_matches if self._validate_pan(pan)]))
        
        # Enhanced DI code extraction
        di_pattern = self.regex_patterns["identifiers"]["di_code"]
        di_matches = re.findall(di_pattern, text_upper)
        # Enhanced DI code filtering with context
        false_positives = {
            'DECEMBER', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE', 'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER',
            'DIVIDEND', 'DOCUMENT', 'DELIVERY', 'DIRECTOR', 'DETAILED', 'DOWNLOAD', 'DOMESTIC', 'DURATION', 'DIFFERENT', 'DIRECTLY'
        }
        di_codes = list(set([di for di in di_matches if di not in false_positives and self._validate_di_code(di, text_upper)]))
        
        # AIF folios: 10 digits starting with 5,6,7,8,9
        aif_pattern = self.regex_patterns["identifiers"]["aif_folio"]
        aif_folios = list(set(re.findall(aif_pattern, text)))
        
        # Account codes: exactly 8 digit numbers (excluding AIF folios and dates)
        account_pattern = self.regex_patterns["identifiers"]["account_code"]
        all_8_digits = set(re.findall(account_pattern, text))
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
        """Validate DI code with relaxed context"""
        if not re.match(r'^D[0-9A-Z]{7}$|^DI[0-9A-Z]{6}$', di):
            return False
        
        # Always accept if it's in a financial context (has keywords like send, statement, etc.)
        financial_context = ['SEND', 'STATEMENT', 'PORTFOLIO', 'REPORT', 'PLEASE', 'FOR', 'ACCOUNT', 'FOLIO', 'CLIENT', 'PAN']
        if any(indicator in context for indicator in financial_context):
            return True
        
        # Fallback: accept if it looks like a proper DI code format
        return True

    def match_statement_types(self, text: str) -> Tuple[List[str], List[str], float]:
        """Enhanced statement type matching with multi-layer scoring"""
        text_lower = text.lower()
        pms_statements = []
        aif_statements = []
        max_confidence = 0.0
        
        # Enhanced "all" patterns with higher confidence
        if any(pattern in text_lower for pattern in self.statement_keywords["all_patterns"]["all_statements"]):
            pms_statements = list(self.statement_keywords["pms"].keys())
            aif_statements = ["AIF_Statement"]
            return pms_statements, aif_statements, 98.0
        
        if any(pattern in text_lower for pattern in self.statement_keywords["all_patterns"]["all_pms"]):
            pms_statements = list(self.statement_keywords["pms"].keys())
            return pms_statements, aif_statements, 97.0
        
        if any(pattern in text_lower for pattern in self.statement_keywords["all_patterns"]["all_aif"]):
            aif_statements = ["AIF_Statement"]
            return pms_statements, aif_statements, 97.0
        
        # Enhanced AIF detection with context scoring
        aif_score = 0
        for keyword in self.statement_keywords["aif"]["AIF_Statement"]["primary"]:
            if keyword in text_lower:
                aif_score = max(aif_score, 95.0)
        for keyword in self.statement_keywords["aif"]["AIF_Statement"]["secondary"]:
            if keyword in text_lower:
                aif_score = max(aif_score, 85.0)
        
        if aif_score > 0:
            aif_statements.append("AIF_Statement")
            max_confidence = max(max_confidence, aif_score)
        
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
            
            if stmt_score >= 60:
                pms_statements.append(stmt_type)
                max_confidence = max(max_confidence, min(98.0, stmt_score))
        
        return pms_statements, aif_statements, max_confidence

    def extract_date_range(self, text: str) -> Tuple[Optional[datetime], Optional[datetime], float]:
        """Advanced date extraction with from/to logic"""
        dates = []
        
        # Find all dates first
        try:
            found_dates = list(datefinder.find_dates(text))
            dates.extend([d for d in found_dates if 1990 <= d.year <= 2050])
        except:
            pass
        
        # Comprehensive Financial Year and Period parsing
        now = datetime.now()
        current_year = now.year
        
        # Financial Year patterns
        fy_patterns = {
            r'\b(current|this)\s+fy\b': lambda: self._get_current_fy(now),
            r'\b(last|previous)\s+fy\b': lambda: self._get_last_fy(now),
            r'\bnext\s+fy\b': lambda: self._get_next_fy(now),
            r'\bfy\s*(\d{2,4})\b': lambda: self._get_specific_fy(re.search(r'\bfy\s*(\d{2,4})\b', text.lower()).group(1))
        }
        
        # Time period patterns
        period_patterns = {
            r'\b(current|this)\s+(year|month|quarter)\b': lambda: self._get_current_period(re.search(r'\b(current|this)\s+(year|month|quarter)\b', text.lower()).group(2), now),
            r'\b(last|previous)\s+(year|month|quarter)\b': lambda: self._get_last_period(re.search(r'\b(last|previous)\s+(year|month|quarter)\b', text.lower()).group(2), now),
            r'\bytd\b|\byear\s+to\s+date\b': lambda: (datetime(current_year, 1, 1).date(), now.date()),
            r'\bmtd\b|\bmonth\s+to\s+date\b': lambda: (now.replace(day=1).date(), now.date()),
            r'\bqtd\b|\bquarter\s+to\s+date\b': lambda: self._get_qtd(now),
            r'\byesterday\b': lambda: ((now - timedelta(days=1)).date(), (now - timedelta(days=1)).date()),
            r'\btoday\b': lambda: (now.date(), now.date()),
            r'\blast\s+(\d+)\s+(days?|months?|years?)\b': lambda: self._get_last_n_period(text.lower(), now)
        }
        
        # Check exact patterns first
        for pattern, handler in {**fy_patterns, **period_patterns}.items():
            if re.search(pattern, text.lower()):
                try:
                    result = handler()
                    if result:
                        return result[0], result[1], 95.0
                except:
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
        
        # Check for "from" pattern
        from_match = re.search(r'from\s+(\S+)', text.lower())
        if from_match and dates:
            return dates[0].date(), datetime.today().date(), 95.0
        
        # Check for date ranges
        if len(dates) >= 2:
            dates.sort()
            return dates[0].date(), dates[-1].date(), 95.0
        elif len(dates) == 1:
            return self.DEFAULT_FROM_DATE, dates[0].date(), 90.0
        
        return self.DEFAULT_FROM_DATE, (datetime.today() - timedelta(days=1)).date(), 0.0
    
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
        return datetime(year - 1, 4, 1).date(), datetime(year, 3, 31).date()
    
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
        match = re.search(r'\blast\s+(\d+)\s+(days?|months?|years?)\b', text)
        if match:
            n = int(match.group(1))
            unit = match.group(2)
            if 'day' in unit:
                start_date = now - timedelta(days=n)
            elif 'month' in unit:
                start_date = now - relativedelta(months=n)
            elif 'year' in unit:
                start_date = now - relativedelta(years=n)
            return start_date.date(), now.date()

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
        """Main parsing function"""
        # Extract identifiers
        identifiers = self.extract_identifiers(text)
        
        # Rule-based parsing
        pms_statements, aif_statements, stmt_confidence = self.match_statement_types(text)
        from_date, to_date, date_confidence = self.extract_date_range(text)
        
        has_identifiers = any(identifiers.values())
        overall_confidence = self.calculate_confidence(stmt_confidence, date_confidence, has_identifiers, identifiers)
        
        # Business logic validation and statement category determination
        statement_category = []
        all_statements = []
        
        # PMS statements - can use any identifier
        if pms_statements:
            statement_category.append("PMS")
            all_statements.extend(pms_statements)
        
        # AIF statements - require AIF folio OR PAN (NOT DI code only)
        if aif_statements:
            has_aif_folio = len(identifiers["aif_folio"]) > 0
            has_pan = len(identifiers["pan_numbers"]) > 0
            has_only_di = len(identifiers["di_code"]) > 0 and not has_aif_folio and not has_pan
            
            if has_aif_folio or has_pan:
                statement_category.append("AIF")
                all_statements.extend(aif_statements)
            elif has_only_di:
                # Remove AIF statements if only DI code is provided
                logger.warning("AIF statements require AIF folio or PAN, not DI code only")
                # Boost PMS confidence since DI code is valid for PMS
                overall_confidence = min(100.0, overall_confidence * 1.1)
        
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
                "parsing_method": "rule_based",
                "model_version": self.model_config["version"],
                "has_identifiers": has_identifiers,
                "business_logic_applied": True
            },
            "raw_text": text
        }