"""Generate annotation templates from automatic detection"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.document_handler import DocumentHandler
from src.redactors import RegexRedactor


def create_annotation_template(doc_path: str, output_path: str):
    """
    Create annotation template from automatic detection
    
    Args:
        doc_path: Path to document
        output_path: Path to save annotation JSON
    """
    print(f"\n{'='*60}")
    print(f"Creating annotation template: {doc_path}")
    print(f"{'='*60}")
    
    # Read document
    doc = DocumentHandler.read_document(doc_path)
    text = DocumentHandler.extract_text(doc)
    
    print(f"Document length: {len(text)} characters")
    
    # Run regex redactor
    redactor = RegexRedactor(consistency_mode=False)
    entities = redactor.detect_pii(text)
    
    print(f"Detected entities: {len(entities)}")
    
    # Get statistics
    stats = redactor.get_statistics()
    print("\nDetected PII by type:")
    for pii_type, count in sorted(stats.items()):
        print(f"  {pii_type}: {count}")
    
    # Create annotations
    annotations = []
    for entity in entities:
        annotation = {
            "text": entity.text,
            "type": entity.type,
            "start": entity.start,
            "end": entity.end,
            "confidence": entity.confidence,
            "document": Path(doc_path).name,
            "verified": False,  # User should verify
            "notes": ""  # User can add notes
        }
        annotations.append(annotation)
    
    # Create template with instructions
    template = {
        "document": Path(doc_path).name,
        "total_detections": len(entities),
        "instructions": [
            "REVIEW INSTRUCTIONS:",
            "1. Check each annotation - is it actually PII?",
            "2. Set 'verified': true if correct, false if wrong (false positive)",
            "3. Add any MISSED PII as new entries",
            "4. Add notes for ambiguous cases",
            "5. Types: email, phone, ssn, credit_card, ip_address, dob, address, person, organization"
        ],
        "statistics": stats,
        "annotations": annotations
    }
    
    # Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Annotation template saved: {output_path}")
    print(f"\n📝 Next steps:")
    print(f"   1. Open {output_path}")
    print(f"   2. Review each annotation")
    print(f"   3. Mark 'verified': true for correct detections")
    print(f"   4. Mark 'verified': false for false positives")
    print(f"   5. Add any missed PII as new entries")
    
    # Show sample annotations
    print(f"\n📄 Sample annotations:")
    for i, ann in enumerate(annotations[:5]):
        print(f"   {i+1}. [{ann['type']}] '{ann['text'][:50]}...' (confidence: {ann['confidence']})")
    
    if len(annotations) > 5:
        print(f"   ... and {len(annotations) - 5} more")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("GROUND TRUTH ANNOTATION GENERATOR")
    print("="*60)
    
    # Documents to annotate
    documents = [
        ("tests/test_data/part_1.docx", "tests/ground_truth/part_1_annotations.json"),
        ("tests/test_data/part_2.docx", "tests/ground_truth/part_2_annotations.json"),
    ]
    
    for doc_path, output_path in documents:
        try:
            create_annotation_template(doc_path, output_path)
        except Exception as e:
            print(f"\n❌ Error processing {doc_path}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ ANNOTATION TEMPLATES CREATED")
    print("="*60)
    print("\n📋 Review the JSON files in tests/ground_truth/")
    print("📝 Mark annotations as verified (true/false)")
    print("➕ Add any missed PII detections")
    print("\nOnce reviewed, run the evaluation script to get metrics!")


if __name__ == "__main__":
    main()
