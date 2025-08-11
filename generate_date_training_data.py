#!/usr/bin/env python3
"""
Comprehensive Date Training Data Generator
Covers all date patterns and expressions for email parsing
"""

import json
import random
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

def generate_date_training_data():
    """Generate comprehensive date training data"""
    
    training_data = []
    
    # Date formats
    date_formats = [
        "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y",  # DD-MM-YYYY
        "%d-%b-%Y", "%d %b %Y", "%d %B %Y",  # DD-MMM-YYYY
        "%B %d, %Y", "%b %d, %Y",            # Month DD, YYYY
        "%Y-%m-%d", "%Y/%m/%d",              # YYYY-MM-DD
        "%d-%m-%y", "%d/%m/%y"               # DD-MM-YY
    ]
    
    # Generate sample dates
    base_date = date.today()
    sample_dates = []
    for i in range(365):
        sample_dates.append(base_date - timedelta(days=i))
        sample_dates.append(base_date + timedelta(days=i))
    
    # 1. Single date patterns
    single_date_patterns = [
        "as on {date}", "as at {date}", "for {date}", "on {date}",
        "dated {date}", "statement for {date}", "report for {date}",
        "position as on {date}", "balance as on {date}", "status as on {date}"
    ]
    
    for pattern in single_date_patterns:
        for _ in range(20):  # 20 samples per pattern
            sample_date = random.choice(sample_dates)
            date_format = random.choice(date_formats)
            formatted_date = sample_date.strftime(date_format)
            
            text = f"Send statement {pattern.format(date=formatted_date)}"
            
            training_data.append({
                "text": text,
                "date_pattern": "single_date",
                "from_date": "1990-01-01",
                "to_date": str(sample_date),
                "confidence": random.uniform(85, 95)
            })
    
    # 2. Date range patterns
    range_patterns = [
        "from {from_date} to {to_date}",
        "between {from_date} and {to_date}",
        "period from {from_date} to {to_date}",
        "during {from_date} to {to_date}",
        "{from_date} to {to_date}",
        "for period {from_date} to {to_date}"
    ]
    
    for pattern in range_patterns:
        for _ in range(15):  # 15 samples per pattern
            from_date = random.choice(sample_dates)
            to_date = from_date + timedelta(days=random.randint(30, 365))
            
            from_format = random.choice(date_formats)
            to_format = random.choice(date_formats)
            
            formatted_from = from_date.strftime(from_format)
            formatted_to = to_date.strftime(to_format)
            
            text = f"Send statement {pattern.format(from_date=formatted_from, to_date=formatted_to)}"
            
            training_data.append({
                "text": text,
                "date_pattern": "date_range",
                "from_date": str(from_date),
                "to_date": str(to_date),
                "confidence": random.uniform(90, 98)
            })
    
    # 3. Financial year patterns
    fy_patterns = [
        "FY {fy1}-{fy2}", "FY {fy1}-{fy2}", "FY{fy1}-{fy2}",
        "financial year {fy1}-{fy2}", "Financial Year {fy1}-{fy2}",
        "FY {fy}", "financial year {fy}",
        "current FY", "current financial year", "this FY", "this financial year",
        "last FY", "previous FY", "last financial year", "previous financial year",
        "next FY", "next financial year"
    ]
    
    current_year = datetime.now().year
    
    for pattern in fy_patterns:
        if "{fy1}" in pattern:
            for year in range(2020, 2026):
                fy1 = str(year)[-2:]
                fy2 = str(year + 1)[-2:]
                text = f"Send statement for {pattern.format(fy1=fy1, fy2=fy2)}"
                
                fy_start = date(year, 4, 1)
                fy_end = date(year + 1, 3, 31)
                
                training_data.append({
                    "text": text,
                    "date_pattern": "financial_year",
                    "from_date": str(fy_start),
                    "to_date": str(fy_end),
                    "confidence": random.uniform(92, 98)
                })
        elif "{fy}" in pattern:
            for year in range(2020, 2026):
                text = f"Send statement for {pattern.format(fy=year)}"
                
                fy_start = date(year, 4, 1)
                fy_end = date(year + 1, 3, 31)
                
                training_data.append({
                    "text": text,
                    "date_pattern": "financial_year",
                    "from_date": str(fy_start),
                    "to_date": str(fy_end),
                    "confidence": random.uniform(92, 98)
                })
        else:
            # Current, last, next FY
            text = f"Send statement for {pattern}"
            
            if "current" in pattern or "this" in pattern:
                if current_year >= 4:
                    fy_start = date(current_year, 4, 1)
                    fy_end = date(current_year + 1, 3, 31)
                else:
                    fy_start = date(current_year - 1, 4, 1)
                    fy_end = date(current_year, 3, 31)
            elif "last" in pattern or "previous" in pattern:
                if current_year >= 4:
                    fy_start = date(current_year - 1, 4, 1)
                    fy_end = date(current_year, 3, 31)
                else:
                    fy_start = date(current_year - 2, 4, 1)
                    fy_end = date(current_year - 1, 3, 31)
            else:  # next
                if current_year >= 4:
                    fy_start = date(current_year + 1, 4, 1)
                    fy_end = date(current_year + 2, 3, 31)
                else:
                    fy_start = date(current_year, 4, 1)
                    fy_end = date(current_year + 1, 3, 31)
            
            training_data.append({
                "text": text,
                "date_pattern": "financial_year",
                "from_date": str(fy_start),
                "to_date": str(fy_end),
                "confidence": random.uniform(92, 98)
            })
    
    # 4. Relative date patterns
    relative_patterns = [
        ("yesterday", -1, "days"),
        ("today", 0, "days"),
        ("last week", -7, "days"),
        ("last month", -1, "months"),
        ("last quarter", -3, "months"),
        ("last year", -1, "years"),
        ("last 3 months", -3, "months"),
        ("last 6 months", -6, "months"),
        ("past 3 months", -3, "months"),
        ("past 6 months", -6, "months"),
        ("previous 3 months", -3, "months"),
        ("this month", 0, "month_start"),
        ("this quarter", 0, "quarter_start"),
        ("this year", 0, "year_start"),
        ("current month", 0, "month_start"),
        ("current quarter", 0, "quarter_start"),
        ("current year", 0, "year_start")
    ]
    
    now = datetime.now()
    
    for pattern, offset, unit in relative_patterns:
        text = f"Send statement for {pattern}"
        
        if unit == "days":
            if offset == 0:  # today
                from_date = to_date = now.date()
            else:
                target_date = now + timedelta(days=offset)
                from_date = to_date = target_date.date()
        elif unit == "months":
            if offset < 0:
                start_date = now + relativedelta(months=offset)
                from_date = start_date.date()
                to_date = now.date()
            else:
                from_date = to_date = now.date()
        elif unit == "years":
            start_date = now + relativedelta(years=offset)
            from_date = start_date.date()
            to_date = now.date()
        elif unit == "month_start":
            from_date = now.replace(day=1).date()
            to_date = now.date()
        elif unit == "quarter_start":
            q = (now.month - 1) // 3 + 1
            start_month = (q - 1) * 3 + 1
            from_date = datetime(now.year, start_month, 1).date()
            to_date = now.date()
        elif unit == "year_start":
            from_date = datetime(now.year, 1, 1).date()
            to_date = now.date()
        
        training_data.append({
            "text": text,
            "date_pattern": "relative_date",
            "from_date": str(from_date),
            "to_date": str(to_date),
            "confidence": random.uniform(88, 95)
        })
    
    # 5. To-date patterns
    to_date_patterns = [
        "YTD", "year to date", "MTD", "month to date", 
        "QTD", "quarter to date", "WTD", "week to date"
    ]
    
    for pattern in to_date_patterns:
        text = f"Send statement for {pattern}"
        
        if "YTD" in pattern or "year to date" in pattern:
            from_date = datetime(now.year, 1, 1).date()
            to_date = now.date()
        elif "MTD" in pattern or "month to date" in pattern:
            from_date = now.replace(day=1).date()
            to_date = now.date()
        elif "QTD" in pattern or "quarter to date" in pattern:
            q = (now.month - 1) // 3 + 1
            start_month = (q - 1) * 3 + 1
            from_date = datetime(now.year, start_month, 1).date()
            to_date = now.date()
        elif "WTD" in pattern or "week to date" in pattern:
            days_since_monday = now.weekday()
            from_date = (now - timedelta(days=days_since_monday)).date()
            to_date = now.date()
        
        training_data.append({
            "text": text,
            "date_pattern": "to_date",
            "from_date": str(from_date),
            "to_date": str(to_date),
            "confidence": random.uniform(90, 96)
        })
    
    # 6. Quarter patterns
    quarter_patterns = [
        "Q1 {year}", "Q2 {year}", "Q3 {year}", "Q4 {year}",
        "1st quarter {year}", "2nd quarter {year}", "3rd quarter {year}", "4th quarter {year}",
        "first quarter {year}", "second quarter {year}", "third quarter {year}", "fourth quarter {year}"
    ]
    
    for pattern in quarter_patterns:
        for year in range(2020, 2026):
            text = f"Send statement for {pattern.format(year=year)}"
            
            if "Q1" in pattern or "1st" in pattern or "first" in pattern:
                from_date = date(year, 1, 1)
                to_date = date(year, 3, 31)
            elif "Q2" in pattern or "2nd" in pattern or "second" in pattern:
                from_date = date(year, 4, 1)
                to_date = date(year, 6, 30)
            elif "Q3" in pattern or "3rd" in pattern or "third" in pattern:
                from_date = date(year, 7, 1)
                to_date = date(year, 9, 30)
            else:  # Q4
                from_date = date(year, 10, 1)
                to_date = date(year, 12, 31)
            
            training_data.append({
                "text": text,
                "date_pattern": "quarter",
                "from_date": str(from_date),
                "to_date": str(to_date),
                "confidence": random.uniform(90, 96)
            })
    
    # 7. Month-year patterns
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    for month in months:
        for year in range(2020, 2026):
            text = f"Send statement for {month} {year}"
            
            month_num = months.index(month) + 1
            from_date = date(year, month_num, 1)
            
            if month_num == 12:
                to_date = date(year, 12, 31)
            else:
                to_date = (date(year, month_num + 1, 1) - timedelta(days=1))
            
            training_data.append({
                "text": text,
                "date_pattern": "month_year",
                "from_date": str(from_date),
                "to_date": str(to_date),
                "confidence": random.uniform(88, 94)
            })
    
    return training_data

def save_date_training_data():
    """Generate and save date training data"""
    data = generate_date_training_data()
    
    with open('training_data/date_training.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Generated {len(data)} date training samples")
    
    # Show pattern distribution
    patterns = {}
    for sample in data:
        pattern = sample['date_pattern']
        patterns[pattern] = patterns.get(pattern, 0) + 1
    
    print("Date pattern distribution:")
    for pattern, count in patterns.items():
        print(f"  {pattern}: {count}")

if __name__ == "__main__":
    import os
    os.makedirs('training_data', exist_ok=True)
    save_date_training_data()