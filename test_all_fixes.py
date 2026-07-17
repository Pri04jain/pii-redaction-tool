"""Test all fixes comprehensively"""
import sys
sys.path.insert(0, '.')
from src.redactors import HybridRedactor

# Test all identified issues
test_text = """
SEBI Registration No: INBI00000004
CIN: L65190GJ1994PLC021012
Firm registration number: 105215W/ W100057
Peer review number: 014680

SEBI regulations under the Companies Act.
BRLM appointed by Underwriters for ASBA.
Anchor Investors and QIB participants.
RoC approved the Red Herring Prospectus.
The Stock Exchange reviewed the Draft Red Herring Prospectus.

ICICI Bank Limited
HDFC Bank Limited
Kotak Mahindra Capital Company Limited

Contact Person: Ashish Mathew Pulloor
Also: Lalit Muljibhai Sarvaiya
"""

print("Testing All Fixes")
print("="*60)

redactor = HybridRedactor()
entities = redactor.detect_pii(test_text)

# Group by type
by_type = {}
for entity in entities:
    entity_type = entity.type
    if entity_type not in by_type:
        by_type[entity_type] = []
    by_type[entity_type].append(entity.text)

print("\n📊 Results by Type:")
for pii_type in sorted(by_type.keys()):
    items = by_type[pii_type]
    print(f"\n{pii_type.upper()} ({len(items)}):")
    for item in items:
        print(f"  - {item}")

print("\n" + "="*60)
print("✅ Expected Results:")
print("  NATIONAL_ID: Should have 2 (SEBI + CIN)")
print("  MEDICAL_LICENSE: Should have 0 (was false positive)")
print("  ORGANIZATION: Should have 3-4 real companies (not 10+)")
print("    Should NOT include: SEBI, BRLM, Underwriters, QIB, RoC,")
print("      Anchor Investors, Stock Exchange, Companies Act")
print("  PERSON: Should have 2 full names:")
print("    - 'Ashish Mathew Pulloor' (NOT split)")
print("    - 'Lalit Muljibhai Sarvaiya' (NOT split)")
