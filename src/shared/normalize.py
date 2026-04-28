from __future__ import annotations

import json
from datetime import date
from typing import Any


def empty_result():
    return {
        "OrderNumber": {"value": None},
        "DeliveryDate": {"value": None},
        "ArticleNumbers": [],
        "DeliveryWeek": {"value": None}
    }


def parse_json_or_empty(raw: Any) -> dict:

    if isinstance(raw, dict):
        return raw

    # Handle case where raw is a JSON string or bytes
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", errors="replace")
    
    # If it's a string, try to parse it as JSON. If parsing fails, return empty result.
    if isinstance(raw, str):
        raw_str = raw.strip()

        if not raw_str:
            return empty_result()
        
        try:
            data = json.loads(raw_str)
        except json.JSONDecodeError:
            return empty_result()
        
        if isinstance(data, dict):
            return data
        else:
            return empty_result()
    
    return empty_result()

# ---- Date normalization functions ----

def date_type(date_string: str) -> date | None:
    if not isinstance(date_string, str):
        return None
    
    date_str = date_string.strip()
    if not date_str:
        return None
    
    # Remove common separators
    if "-" in date_str or "/" in date_str or "." in date_str:
        date_str = date_str.replace("-", "").replace("/", "").replace(".", "")

    #
    if len(date_str) == 6:
        return _date_six_digits(date_str)
    
    if len(date_str) == 8:
        return _date_eight_digits(date_str)
    
    return None


def week_to_date(week_string: str):
    if not isinstance(week_string, str):
        return None
    
    week_str = week_string.strip()
    if not week_str:
        return None
    
    # Take the part after the last dash, e.g. "2023-W15" -> "W15"
    if "-" in week_str:
        week_str = week_str.split("-")[-1]  
    
    # Extract digits from the string
    digits = ""
    for ch in week_str:
        if ch.isdigit():
            digits += ch

    if not digits:
        return None
    
    if len(digits) > 2:
        digits = digits[-2:]  # Take last two digits, e.g. "2023W15" -> "15"
    try:
        week_num = int(digits)
        if week_num < 1 or week_num > 53:
            return None
    except ValueError:
        return None
    
    return week_num
'''
    y = year if year is not None else date.today().year
    try:
        return date.fromisocalendar(y, week_num, 5)  # Return the Friday of the given week
    except ValueError:
        return None
'''

def _date_six_digits(date_string: str) -> date | None:
    today = date.today()
    
    version1 = None
    try: 
        yy = int(date_string[:2])
        mm = int(date_string[2:4])
        dd = int(date_string[4:6])
        version1 = date(2000 + yy, mm, dd)
    except ValueError:
        pass

    version2 = None
    try: 
        dd = int(date_string[:2])
        mm = int(date_string[2:4])
        yy = int(date_string[4:6])
        version2 = date(2000 + yy, mm, dd)
    except ValueError:
        pass

    if version1 and not version2:
        return version1

    if version2 and not version1:
        return version2

    if version1 and version2:
        if abs((version1 - today).days) < abs((version2 - today).days):
            return version1
        else:
            return version2
        

def _date_eight_digits(date_string: str) -> date | None:
    today = date.today()
    
    version1 = None
    try: 
        yyyy = int(date_string[:4])
        mm = int(date_string[4:6])
        dd = int(date_string[6:8])
        version1 = date(yyyy, mm, dd)
    except ValueError:
        pass

    version2 = None
    try: 
        dd = int(date_string[:2])
        mm = int(date_string[2:4])
        yyyy = int(date_string[4:8])
        version2 = date(yyyy, mm, dd)
    except ValueError:
        pass

    if version1 and not version2:
        return version1

    if version2 and not version1:
        return version2

    if version1 and version2:
         #abs för att gamla datum ska kunna fångas och visa fel
        if abs((version1 - today).days) < abs((version2 - today).days):
            return version1
        else:
            return version2


def _clean_multiline_value(value: str) -> str:
    parts = []

    for p in value.splitlines():
        cleaned = p.strip()
        if cleaned:
            parts.append(cleaned)

    if not parts:
        return ""
    
    if len(set(parts)) == 1:
        return parts[0]
    
    return parts[0]


def process_json(data: dict) -> dict:
    
    try:
        date_val = data.get("DeliveryDate", {}).get("value")
        week_val = data.get("DeliveryWeek", {}).get("value")
    except AttributeError:
        return data
    
    if isinstance(date_val, str) and date_val.strip():
        cleaned_date_val = _clean_multiline_value(date_val)
        date_t = date_type(cleaned_date_val)
        if date_t:
            data["DeliveryDate"]["value"] = date_t.isoformat()
    
    if isinstance(week_val, str) and week_val.strip():
        week_t = week_to_date(week_val)
        if week_t:
            data["DeliveryWeek"]["value"] = week_t
    
    return data


def canonicalize_json(raw_output: Any, source: str) -> dict:
    """
    For sources that are expected to return JSON, attempt to parse it. If parsing fails, return an empty result instead of crashing.
    """
    if source in ("ollama", "openai", "azure", "claude", "google"):
        data = parse_json_or_empty(raw_output)
        return process_json(data)
    
    raise ValueError(f"Unknown source for cannonicalization: {source}")