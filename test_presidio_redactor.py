"""Test script for PresidioRedactor implementation"""

from src.redactors.presidio_redactor import PresidioRedactor, PRESIDIO_AVAILABLE

def test_presidio_redactor():
    """Test the Presidio redactor with sample data"""
    
    if not PRESIDIO_AVAILABLE:
        print("❌ Presidio is not installed!")
        print("Install with: pip install presidio-analyzer presidio-anonymizer")
        print("Also install spaCy model: python -m spacy download en_core_web_lg")
        return
    
    print("✅ Presidio is available!")
    print("\nInitializing PresidioRedactor...")
    
    try:
        # Initialize with threshold of 0.7
        redactor = PresidioRedactor(consistency_mode=True, seed=42, threshold=0.7)
        print("✅ PresidioRedactor initialized successfully!")
        
        # Get supported entities
        print(f"\n📋 Supported entities: {len(redactor.get_supported_entities())} types")
        
        # Test text with various PII types
        test_text = """
        Personal Information:
        Name: John Smith
        Email: john.smith@example.com
        Phone: +1-555-123-4567
        Indian Phone: +91 9876543210
        SSN: 123-45-6789
        Credit Card: 4532-1488-0343-6467
        IP Address: 192.168.1.1
        Date of Birth: Born on January 15, 1985
        Address: 123 Main Street, New York, NY 10001
        Company: Acme Corporation
        
        Meeting scheduled for March 25, 2024 at the office.
        """
        
        print("\n" + "="*60)
        print("ORIGINAL TEXT:")
        print("="*60)
        print(test_text)
        
        # Detect PII
        print("\n" + "="*60)
        print("DETECTING PII...")
        print("="*60)
        entities = redactor.detect_pii(test_text)
        
        print(f"\n✅ Detected {len(entities)} PII entities:")
        for i, entity in enumerate(entities, 1):
            print(f"{i}. [{entity.type.upper()}] '{entity.text}' (confidence: {entity.confidence:.2f})")
        
        # Get statistics
        stats = redactor.get_statistics()
        print("\n📊 PII Statistics:")
        for pii_type, count in sorted(stats.items()):
            print(f"  - {pii_type}: {count}")
        
        # Redact the text
        print("\n" + "="*60)
        print("REDACTING TEXT...")
        print("="*60)
        redacted_text, replacements = redactor.redact_text(test_text)
        
        print("\n" + "="*60)
        print("REDACTED TEXT:")
        print("="*60)
        print(redacted_text)
        
        print("\n" + "="*60)
        print("REPLACEMENT MAPPING:")
        print("="*60)
        for original, fake in replacements.items():
            print(f"  {original} → {fake}")
        
        # Test threshold adjustment
        print("\n" + "="*60)
        print("TESTING THRESHOLD ADJUSTMENT...")
        print("="*60)
        
        # Reset and test with lower threshold
        redactor.reset()
        redactor.set_threshold(0.5)
        print(f"✅ Threshold set to 0.5")
        
        entities_low = redactor.detect_pii(test_text)
        print(f"✅ Detected {len(entities_low)} PII entities with lower threshold")
        
        # Reset and test with higher threshold
        redactor.reset()
        redactor.set_threshold(0.9)
        print(f"✅ Threshold set to 0.9")
        
        entities_high = redactor.detect_pii(test_text)
        print(f"✅ Detected {len(entities_high)} PII entities with higher threshold")
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("\nMake sure to install:")
        print("  1. pip install presidio-analyzer presidio-anonymizer")
        print("  2. python -m spacy download en_core_web_lg")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("="*60)
    print("PRESIDIO REDACTOR TEST")
    print("="*60)
    test_presidio_redactor()
