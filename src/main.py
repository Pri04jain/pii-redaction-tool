"""CLI interface for PII Redaction Tool"""
import argparse
import sys
from pathlib import Path
from docx import Document
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.document_handler import DocumentHandler
from src.config import Config

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="PII Redaction Tool - Redact sensitive information from documents")
    
    parser.add_argument("-i", "--input", required=True, help="Input DOCX file path")
    parser.add_argument("-o", "--output", required=True, help="Output DOCX file path")
    parser.add_argument("-m", "--mode", 
                       choices=["regex", "ner", "presidio", "hybrid"],
                       default="hybrid",
                       help="Redaction mode (default: hybrid)")
    parser.add_argument("--mapping", help="Save redaction mapping to JSON file")
    parser.add_argument("--stats", action="store_true", help="Show redaction statistics")
    parser.add_argument("--no-consistency", action="store_true", 
                       help="Disable consistent replacements")
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        return 1
    
    print(f"Loading document: {args.input}")
    doc = DocumentHandler.read_document(args.input)
    
    print(f"Using {args.mode} redaction mode...")
    
    # Import appropriate redactor
    if args.mode == "regex":
        from src.redactors.regex_redactor import RegexRedactor
        redactor = RegexRedactor(consistency_mode=not args.no_consistency)
    elif args.mode == "ner":
        from src.redactors.ner_redactor import NERRedactor
        redactor = NERRedactor(consistency_mode=not args.no_consistency)
    elif args.mode == "presidio":
        from src.redactors.presidio_redactor import PresidioRedactor
        redactor = PresidioRedactor(consistency_mode=not args.no_consistency)
    else:  # hybrid
        from src.redactors.hybrid_redactor import HybridRedactor
        redactor = HybridRedactor(consistency_mode=not args.no_consistency)
    
    print("Redacting document...")
    redacted_doc, replacements = redactor.redact_document(doc)
    
    print(f"Saving redacted document: {args.output}")
    DocumentHandler.save_document(redacted_doc, args.output)
    
    # Save mapping if requested
    if args.mapping:
        with open(args.mapping, 'w', encoding='utf-8') as f:
            json.dump(replacements, f, indent=2, ensure_ascii=False)
        print(f"Redaction mapping saved: {args.mapping}")
    
    # Show statistics if requested
    if args.stats:
        stats = redactor.get_statistics()
        print("\nRedaction Statistics:")
        print("-" * 40)
        for pii_type, count in sorted(stats.items()):
            print(f"{pii_type:<20}: {count:>5}")
        print("-" * 40)
        print(f"{'Total':<20}: {sum(stats.values()):>5}")
    
    print("\n✅ Redaction completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
