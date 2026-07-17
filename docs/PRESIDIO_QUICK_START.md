# Presidio Redactor Quick Start Guide

## Installation

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Download spaCy English language model
python -m spacy download en_core_web_lg
```

## Basic Usage

### 1. Import and Initialize

```python
from src.redactors.presidio_redactor import PresidioRedactor

# Create redactor instance
redactor = PresidioRedactor(
    consistency_mode=True,  # Same PII → Same fake value
    seed=42,                # For reproducible results
    threshold=0.7           # Confidence threshold (0.0-1.0)
)
```

### 2. Detect PII

```python
text = "Contact John Smith at john@example.com or call +91 9876543210"

# Detect PII entities
entities = redactor.detect_pii(text)

# View detected entities
for entity in entities:
    print(f"{entity.type}: {entity.text} ({entity.confidence:.2f})")
```

Output:
```
person: John Smith (0.85)
email: john@example.com (0.95)
phone: +91 9876543210 (0.85)
```

### 3. Redact Text

```python
# Redact PII
redacted_text, replacements = redactor.redact_text(text)

print("Redacted:", redacted_text)
print("Mapping:", replacements)
```

Output:
```
Redacted: Contact Lisa Johnson at lisa@example.org or call +91 8765432109
Mapping: {
    'John Smith': 'Lisa Johnson',
    'john@example.com': 'lisa@example.org',
    '+91 9876543210': '+91 8765432109'
}
```

### 4. Redact Documents

```python
from docx import Document

# Load document
doc = Document("input.docx")

# Redact
redacted_doc, replacements = redactor.redact_document(doc)

# Save
redacted_doc.save("output.docx")
```

## Supported PII Types

| Category | Types |
|----------|-------|
| **Identity** | PERSON, US_SSN, US_DRIVER_LICENSE, US_PASSPORT |
| **Contact** | EMAIL_ADDRESS, PHONE_NUMBER, INDIAN_PHONE_NUMBER |
| **Financial** | CREDIT_CARD, IBAN_CODE, US_BANK_NUMBER |
| **Location** | LOCATION (addresses), IP_ADDRESS |
| **Organization** | ORGANIZATION (companies) |
| **Temporal** | DATE_TIME (filtered for DOB context) |
| **Other** | URL, MEDICAL_LICENSE, NRP |

## Adjusting Threshold

```python
# More precise, fewer detections
redactor.set_threshold(0.9)

# More sensitive, more detections
redactor.set_threshold(0.5)
```

**Recommended thresholds:**
- `0.9+`: High precision mode
- `0.7-0.8`: Balanced (default)
- `0.5-0.6`: High recall mode

## Statistics

```python
# Get detection counts
stats = redactor.get_statistics()
print(stats)
# {'person': 2, 'email': 1, 'phone': 3}
```

## Reset State

```python
# Clear caches and start fresh
redactor.reset()
```

## Error Handling

```python
from src.redactors.presidio_redactor import PRESIDIO_AVAILABLE

if not PRESIDIO_AVAILABLE:
    print("Presidio not installed!")
    # Use fallback redactor
else:
    redactor = PresidioRedactor()
```

## Common Issues

### Issue: "spaCy model not found"
**Solution:**
```bash
python -m spacy download en_core_web_lg
```

### Issue: "ImportError: presidio_analyzer"
**Solution:**
```bash
pip install presidio-analyzer presidio-anonymizer
```

### Issue: Dates being redacted incorrectly
**Solution:** The redactor uses context filtering for dates. Only dates near DOB keywords are redacted as DOB.

## Examples

### Example 1: Email Redaction
```python
text = "Send report to admin@company.com and cc: manager@company.com"
redacted, mapping = redactor.redact_text(text)
# Both emails consistently replaced
```

### Example 2: Multi-language Phones
```python
text = "US: +1-555-123-4567, India: +91 9876543210"
entities = redactor.detect_pii(text)
# Both detected with appropriate confidence scores
```

### Example 3: Batch Processing
```python
documents = ["doc1.txt", "doc2.txt", "doc3.txt"]

for doc_path in documents:
    with open(doc_path) as f:
        text = f.read()
    
    redacted, _ = redactor.redact_text(text)
    
    with open(f"redacted_{doc_path}", "w") as f:
        f.write(redacted)
```

## Performance Tips

1. **Reuse redactor instance** - Avoid reinitializing for better performance
2. **Batch process** - Process multiple texts with same redactor
3. **Set appropriate threshold** - Higher threshold = faster processing
4. **Use consistency mode** - Reduces repeated fake data generation

## Testing

```bash
# Run test script
python test_presidio_redactor.py
```

## Comparison: Regex vs Presidio

| Aspect | Regex | Presidio |
|--------|-------|----------|
| Speed | ⚡ Fast | 🐢 Moderate |
| Accuracy | ✓ Good | ✓✓ High |
| Context-aware | ✗ No | ✓ Yes |
| Setup | ✓ Easy | ⚙️ Moderate |

**When to use Presidio:**
- Need high accuracy
- Complex document types
- Context matters (e.g., DOB vs regular dates)
- Multiple PII types in same text

**When to use Regex:**
- Need speed
- Simple, structured data
- Known PII formats
- Real-time processing

## Next Steps

- Read full documentation: `PRESIDIO_REDACTOR_IMPLEMENTATION.md`
- Check base class: `src/redactors/base_redactor.py`
- Add custom recognizers for your domain
- Tune threshold for your use case

## Support

For issues or questions:
1. Check documentation
2. Run test script
3. Review error messages
4. Check Presidio docs: https://microsoft.github.io/presidio/
