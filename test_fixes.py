"""Test all the fixes we implemented"""
import sys
sys.path.insert(0, '.')
from src.redactors import HybridRedactor

# Test text with various PII types
test_text = """
ICICI Bank Limited
163, 5th Floor, H.T.Parekh Marg
Backbay Reclamation Churchgate, Mumbai – 400020
Telephone: 022-68052182
Email: ipocmg@icicibank.com
Website: www.icicibank.com
Contact Person: Amit Chitale/ Arvind Rane/ Rakesh Iyer

This consent is dated December 3, 2025.
The examination report dated November 5, 2025 was reviewed.

SEBI regulations require compliance with the Companies Act.
The BSE and NSE are Stock Exchanges in India.

John Smith was born on March 15, 1985.
His date of birth: 15/03/1985
"""

print("Testing Hybrid Redactor with Fixes")
print("="*60)

redactor = HybridRedactor()
entities = redactor.detect_pii(test_text)

print(f"\nTotal entities detected: {len(entities)}")
print("\nBreakdown by type:")

# Group by type
by_type = {}
for entity in entities:
    entity_type = entity.type
    if entity_type not in by_type:
        by_type[entity_type] = []
    by_type[entity_type].append(entity.text)

for pii_type, items in sorted(by_type.items()):
    print(f"\n{pii_type.upper()} ({len(items)}):")
    for item in items:
        print(f"  - {item}")

print("\n" + "="*60)
print("Expected improvements:")
print("✓ DOB: Should ONLY detect '15/03/1985' with 'date of birth' context")
print("  (NOT 'December 3, 2025' or 'November 5, 2025')")
print("✓ Organization: Should NOT detect 'SEBI', 'BSE', 'NSE', 'Companies Act'")
print("  (ONLY 'ICICI Bank Limited')")
print("✓ Person: Should detect 'Amit Chitale', 'Arvind Rane', 'Rakesh Iyer', 'John Smith'")
print("  (Label should be 'person' not 'name')")
print("✓ Location: Standalone 'Mumbai', 'India' should be filtered")
print("  (ONLY full address should be kept)")
