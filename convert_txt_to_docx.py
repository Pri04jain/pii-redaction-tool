"""Convert sample test document from TXT to DOCX"""
from docx import Document

# Read the text file
with open('tests/test_data/sample_test_document.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Create a new Word document
doc = Document()

# Add the text (preserving line breaks)
for line in text.split('\n'):
    doc.add_paragraph(line)

# Save as DOCX
doc.save('tests/test_data/sample_test_document.docx')

print("✅ Converted sample_test_document.txt → sample_test_document.docx")
print("📍 Location: tests/test_data/sample_test_document.docx")
