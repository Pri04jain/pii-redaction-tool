"""
Verify that all 9 required PII detectors are working
"""
import sys
sys.path.insert(0, '.')
from src.redactors import RegexRedactor, PresidioRedactor, HybridRedactor

# Test text with all 9 required PII types
test_text = """
Contact: John Michael Smith
Email: john.smith@example.com
Phone: +1-555-123-4567 or (555) 987-6543
Company: Acme Corporation and XYZ Bank Limited

Address: 123 Main Street, Apt 4B, New York, NY 10001
Also: P.O. Box 456, Los Angeles, CA 90001

SSN: 123-45-6789
Credit Card: 4532-1234-5678-9010
DOB: Born on 01/15/1980, also March 25, 1975 is a date of birth
IP Address: 192.168.1.1 and 10.0.0.254
"""

print("="*60)
print("VERIFYING ALL 9 REQUIRED PII DETECTORS")
print("="*60)

redactors = [
    ("Regex", RegexRedactor()),
    ("Presidio", PresidioRedactor()),
    ("Hybrid", HybridRedactor()),
]

REQUIRED_TYPES = {
    'person': 'Full names',
    'email': 'Email addresses',
    'phone': 'Phone numbers',
    'organization': 'Company names',
    'address': 'Physical/mailing addresses',
    'location': 'Physical/mailing addresses',  # Merged
    'ssn': 'Social Security Numbers',
    'credit_card': 'Credit card numbers',
    'dob': 'Dates of birth',
    'ip_address': 'IP addresses',
}

for name, redactor in redactors:
    print(f"\n{'='*60}")
    print(f"{name} Redactor")
    print(f"{'='*60}")
    
    try:
        entities = redactor.detect_pii(test_text)
        
        # Group by type
        by_type = {}
        for entity in entities:
            entity_type = entity.type.lower().replace('_', ' ').strip()
            
            # Map to required type
            required_type = None
            for internal, req in REQUIRED_TYPES.items():
                if internal in entity_type or entity_type in internal:
                    required_type = req
                    break
            
            if required_type:
                if required_type not in by_type:
                    by_type[required_type] = []
                by_type[required_type].append(entity.text)
        
        # Check coverage of all 9 types
        all_required = set(REQUIRED_TYPES.values())
        detected_types = set(by_type.keys())
        missing_types = all_required - detected_types
        
        print(f"\nDetected {len(detected_types)}/9 required types:")
        for req_type in sorted(all_required):
            if req_type in by_type:
                count = len(by_type[req_type])
                print(f"  ✅ {req_type}: {count} detected")
                # Show examples
                for item in by_type[req_type][:2]:
                    print(f"      - {item}")
            else:
                print(f"  ❌ {req_type}: 0 detected")
        
        if missing_types:
            print(f"\n⚠️  WARNING: Missing detectors for:")
            for mt in sorted(missing_types):
                print(f"      - {mt}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print("SUMMARY")
print(f"{'='*60}")
print("\nExpected: All 9 types detected by Hybrid Redactor")
print("  - Full names, Email, Phone, Company, Address")
print("  - SSN, Credit Card, DOB, IP Address")
print("\nIf any type shows 0 detections:")
print("  1. Check if detector is implemented")
print("  2. Check if it's wired into detect_pii() method")
print("  3. Check if patterns/recognizers are working")
