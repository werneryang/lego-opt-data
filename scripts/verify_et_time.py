from datetime import datetime
from zoneinfo import ZoneInfo
import sys
import os

# Add src to path
sys.path.append(os.path.abspath("src"))

from opt_data.util.calendar import to_et_date

def test_et_conversion():
    # 1. Current time (Aware UTC)
    now_utc = datetime.now(ZoneInfo("UTC"))
    et_date = to_et_date(now_utc)
    print(f"Now UTC: {now_utc}")
    print(f"ET Date: {et_date}")
    
    # 2. Edge case: Late night UTC (e.g., 03:00 UTC next day = 22:00 ET previous day)
    # Construct a specific time
    late_utc = datetime(2025, 11, 29, 3, 0, 0, tzinfo=ZoneInfo("UTC"))
    et_date_late = to_et_date(late_utc)
    print(f"\nLate UTC: {late_utc}")
    print(f"ET Date: {et_date_late}")
    
    expected_date = datetime(2025, 11, 28).date()
    if et_date_late == expected_date:
        print("PASS: Late night conversion correct")
    else:
        print(f"FAIL: Expected {expected_date}, got {et_date_late}")

if __name__ == "__main__":
    test_et_conversion()
