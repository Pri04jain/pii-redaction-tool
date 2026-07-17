"""Debug person name detection"""
import sys
sys.path.insert(0, '.')
from src.redactors import PresidioRedactor, NERRedactor

test_text = "Contact Person: Ashish Mathew Pulloor and Lalit Muljibhai Sarvaiya"

print("Testing Person Name Detection")
print("="*60)

print("\n1. Presidio Detection:")
presidio = PresidioRedactor()
presidio_entities = presidio.detect_pii(test_text)
for entity in presidio_entities:
    if entity.type == 'person':
        print(f"  - '{entity.text}' (start:{entity.start}, end:{entity.end})")

print("\n2. NER Detection:")
try:
    ner = NERRedactor()
    ner_entities = ner.detect_pii(test_text)
    for entity in ner_entities:
        if entity.type == 'person':
            print(f"  - '{entity.text}' (start:{entity.start}, end:{entity.end})")
except Exception as e:
    print(f"  NER failed: {e}")

print("\n" + "="*60)
print("Expected: 2 person names")
print("  - Ashish Mathew Pulloor")
print("  - Lalit Muljibhai Sarvaiya")
