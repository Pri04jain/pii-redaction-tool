"""Test if Presidio can detect organizations"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.redactors import PresidioRedactor

text = """
This document contains company names:
- Acme Corporation handles distribution
- Microsoft Corporation provided software
- Goldman Sachs manages investments
- Tech Innovations LLC is our partner
"""

redactor = PresidioRedactor()
entities = redactor.detect_pii(text)

print("Detected entities:")
for e in entities:
    print(f"  {e.type:20} | {e.text:30} | confidence: {e.confidence:.2f}")

# Check what entities Presidio analyzer supports
print("\nSupported entity types by Presidio:")
print(redactor.analyzer.get_supported_entities())
