"""Check what Hybrid detects in part_2.docx"""
import sys
sys.path.insert(0, '.')
from src.utils.document_handler import DocumentHandler
from src.redactors import HybridRedactor

print('Analyzing part_2.docx with Hybrid Redactor...')
print('='*60)

doc = DocumentHandler.read_document('tests/test_data/part_2.docx')
text = DocumentHandler.extract_text(doc)

print(f'File size: {len(text)} characters')
print(f'Paragraphs: {len(doc.paragraphs)}')

redactor = HybridRedactor()

# Process the entire document (not just extracted text) to accumulate stats properly
redacted_doc, replacements = redactor.redact_document(doc)
stats = redactor.get_statistics()

print(f'\n🎯 Total entities detected: {sum(stats.values())}')
print(f'\n📊 Breakdown by type:')
for pii_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f'  • {pii_type}: {count}')

print('\n' + '='*60)
print(f'✅ EXPECTED TOTAL REDACTIONS: {sum(stats.values())}')
