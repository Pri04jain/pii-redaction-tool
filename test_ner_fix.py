"""Test if NER is now working in Hybrid mode"""
import sys
sys.path.insert(0, '.')
from src.utils.document_handler import DocumentHandler
from src.redactors import HybridRedactor

print('Testing NER fix with part_2.docx...')
print('='*60)

doc = DocumentHandler.read_document('tests/test_data/part_2.docx')

redactor = HybridRedactor()

# Check if NER initialized successfully
if redactor.ner_redactor is not None:
    print('[SUCCESS] NER redactor initialized!')
else:
    print('[FAILED] NER redactor is None')

# Process document
redacted_doc, replacements = redactor.redact_document(doc)
stats = redactor.get_statistics()

print(f'\nTotal entities: {sum(stats.values())}')
print(f'\nBreakdown:')
for pii_type, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
    print(f'  {pii_type}: {count}')

print('\n' + '='*60)
if redactor.ner_redactor:
    print('[FIXED] NER is now working in Hybrid mode!')
else:
    print('[ISSUE] NER still not initialized')
