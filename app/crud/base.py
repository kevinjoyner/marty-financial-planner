from datetime import datetime

def _parse_date(date_val):
    """Parses a date string (YYYY-MM-DD) into a python date object if necessary."""
    if isinstance(date_val, str):
        try:
            return datetime.strptime(date_val, "%Y-%m-%d").date()
        except ValueError:
            return None 
    return date_val
