"""Debug organization detection on IPO document"""
import sys
sys.path.insert(0, '.')
from src.redactors import HybridRedactor

# Sample text from IPO prospectus with regulatory terms
test_text = """
SEBI regulations require compliance under the Companies Act.
The BSE and NSE Stock Exchanges reviewed the Red Herring Prospectus.
BRLM appointed by the Underwriters for the ASBA process.
Anchor Investors and QIB participants registered through SCSB.
The RoC approved the Draft Red Herring Prospectus.

ICICI Bank Limited
HDFC Bank Limited  
Kotak Mahindra Capital Company Limited
IIFL Securities Limited

Contact Person: Ashish Mathew Pulloor
Also: Lalit Muljibhai Sarvaiya
"""

print("Testing Hybrid Redactor - Organization Detection")
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

print("\nORGANIZATION entities:")
if 'organization' in by_type:
    for org in by_type['organization']:
        print(f"  - {org}")
else:
    print("  (none)")

print("\nPERSON entities:")
if 'person' in by_type:
    for person in by_type['person']:
        print(f"  - {person}")
else:
    print("  (none)")

print("\n" + "="*60)
print(f"Total organizations: {len(by_type.get('organization', []))}")
print(f"Total persons: {len(by_type.get('person', []))}")
