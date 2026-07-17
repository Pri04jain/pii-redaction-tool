"""Check what's in part_6.docx"""
import sys
sys.path.insert(0, '.')
from src.utils.document_handler import DocumentHandler
from src.redactors import HybridRedactor

print('Analyzing part_6.docx...')
print('='*60)

doc = DocumentHandler.read_document('tests/test_data/part_6.docx')
text = DocumentHandler.extract_text(doc)

print(f'File size: {len(text)} characters')
print(f'Paragraphs: {len(doc.paragraphs)}')
print(f'\nFirst 1000 characters:')
print(text[:1000])
print('\n' + '='*60)

redactor = HybridRedactor()
entities = redactor.detect_pii(text)
stats = redactor.get_statistics()

print(f'\nEntities detected: {len(entities)}')
print(f'Stats: {stats}')

if len(entities) < 5:
    print('\n⚠️ WARNING: Very few entities detected!')
    print('This file may contain mostly non-PII content (legal text, disclaimers, etc.)')
