"""Test script for NER Redactor"""
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.redactors.ner_redactor import NERRedactor

def test_ner_redactor():
    """Test the NER Redactor implementation"""
    
    print("="*80)
    print("Testing NER Redactor")
    print("="*80)
    
    # Check if spaCy model is available
    try:
        redactor = NERRedactor(consistency_mode=True, confidence_threshold=0.7)
        print("\n✓ NER Redactor initialized successfully")
        
        # Print model info
        model_info = redactor.get_model_info()
        print(f"\nModel Information:")
        print(f"  - Name: {model_info['model_name']}")
        print(f"  - Version: {model_info['model_version']}")
        print(f"  - Language: {model_info['language']}")
        print(f"  - Pipeline: {model_info['pipeline']}")
        
    except ImportError as e:
        print(f"\n✗ Error: {e}")
        return False
    except OSError as e:
        print(f"\n✗ Error: {e}")
        print("\nTo install the required model, run:")
        print("  python -m spacy download en_core_web_lg")
        return False
    
    # Test cases
    test_texts = [
        {
            "name": "Person Names",
            "text": "John Smith works at Microsoft. Contact Mary Johnson for details."
        },
        {
            "name": "Email and Phone",
            "text": "Email me at john.doe@example.com or call +1-555-123-4567."
        },
        {
            "name": "Organizations",
            "text": "Apple Inc. and Google LLC are tech giants based in California."
        },
        {
            "name": "Date of Birth Context",
            "text": "Patient was born on January 15, 1985. The appointment is on March 20, 2024."
        },
        {
            "name": "Mixed PII",
            "text": "Jane Doe (jane@company.com) from Acme Corporation called at 555-9876 regarding the invoice."
        },
        {
            "name": "Location with GPE",
            "text": "Our office is located in New York City, near Central Park."
        },
        {
            "name": "False Positive Test",
            "text": "The Order was processed by the Customer Support Team in January."
        }
    ]
    
    print("\n" + "="*80)
    print("Running Test Cases")
    print("="*80)
    
    for test in test_texts:
        print(f"\n{'='*80}")
        print(f"Test: {test['name']}")
        print(f"{'='*80}")
        print(f"\nOriginal Text:\n  {test['text']}")
        
        # Detect PII
        entities = redactor.detect_pii(test['text'])
        
        if entities:
            print(f"\nDetected Entities ({len(entities)}):")
            for entity in entities:
                print(f"  - [{entity.type.upper()}] '{entity.text}' "
                      f"(confidence: {entity.confidence:.2f}, pos: {entity.start}-{entity.end})")
        else:
            print("\nNo PII detected.")
        
        # Redact text
        redacted_text, replacements = redactor.redact_text(test['text'])
        
        print(f"\nRedacted Text:\n  {redacted_text}")
        
        if replacements:
            print(f"\nReplacements:")
            for original, fake in replacements.items():
                print(f"  '{original}' → '{fake}'")
    
    # Test statistics
    print("\n" + "="*80)
    print("Statistics")
    print("="*80)
    stats = redactor.get_statistics()
    if stats:
        print("\nPII Types Detected:")
        for pii_type, count in stats.items():
            print(f"  - {pii_type}: {count}")
    else:
        print("\nNo statistics available.")
    
    print("\n" + "="*80)
    print("✓ All tests completed successfully!")
    print("="*80)
    
    return True

if __name__ == "__main__":
    success = test_ner_redactor()
    sys.exit(0 if success else 1)
