"""Debug medical license detection"""
import sys
sys.path.insert(0, '.')
from presidio_analyzer import AnalyzerEngine

# Test strings from the document
test_strings = [
    "Firm registration number: 105215W/ W100057",
    "Peer review number: 014680",
    "SEBI Registration No: INBI00000004",
    "CIN: L65190GJ1994PLC021012",
]

analyzer = AnalyzerEngine()

print("Testing Presidio Medical License Detection")
print("="*60)

for test_str in test_strings:
    print(f"\nTest: {test_str}")
    results = analyzer.analyze(text=test_str, language='en', score_threshold=0.0)
    
    for result in results:
        print(f"  Found: {result.entity_type} (score: {result.score:.2f})")
        print(f"  Text: {test_str[result.start:result.end]}")

print("\n" + "="*60)
print("\nListing all built-in Presidio recognizers:")
for recognizer in analyzer.registry.recognizers:
    print(f"  - {recognizer.name}: {recognizer.supported_entities}")
