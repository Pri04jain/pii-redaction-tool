"""Debug DOB detection"""
import sys
sys.path.insert(0, '.')

test_text = """This consent is dated December 3, 2025.
The examination report dated November 5, 2025 was reviewed.

John Smith was born on March 15, 1985.
His date of birth: 15/03/1985
"""

# Check what context is near each date
dates = [
    ("December 3, 2025", test_text.find("December 3, 2025")),
    ("November 5, 2025", test_text.find("November 5, 2025")),
    ("March 15, 1985", test_text.find("March 15, 1985")),
]

DOB_KEYWORDS = ['birth', 'born', 'dob', 'd.o.b', 'date of birth', 'birthday', 'age', 'born on', 'years old']

for date, start in dates:
    context_start = max(0, start - 50)
    context_end = min(len(test_text), start + len(date) + 50)
    context = test_text[context_start:context_end].lower()
    
    print(f"\nDate: {date}")
    print(f"Context: '{context}'")
    
    has_keyword = any(kw in context for kw in DOB_KEYWORDS)
    print(f"Has DOB keyword: {has_keyword}")
    
    if has_keyword:
        found_keywords = [kw for kw in DOB_KEYWORDS if kw in context]
        print(f"  Found: {found_keywords}")
