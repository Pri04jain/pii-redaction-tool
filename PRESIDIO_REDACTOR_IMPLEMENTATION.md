# Presidio Redactor Implementation

## Overview

The `PresidioRedactor` is a comprehensive PII detection and redaction implementation using Microsoft's Presidio framework. It provides high-accuracy PII detection using pre-trained NLP models and custom recognizers.

## Features

### Core Capabilities
- **Comprehensive PII Detection**: Leverages Presidio's pre-trained models for accurate entity recognition
- **Custom Recognizers**: Includes specialized recognizers for Indian phone numbers
- **Configurable Threshold**: Adjustable confidence threshold for entity detection (default: 0.7)
- **Consistent Replacements**: Maintains consistent fake data for repeated PII values
- **Entity Scoring**: Provides confidence scores for each detected entity
- **Error Handling**: Graceful fallback when Presidio dependencies are not available

### Supported PII Types

#### Standard Entities (from Presidio)
- **PERSON** → person names
- **EMAIL_ADDRESS** → email addresses
- **PHONE_NUMBER** → phone numbers (US and international)
- **US_SSN** → Social Security Numbers
- **CREDIT_CARD** → credit card numbers
- **IP_ADDRESS** → IP addresses
- **DATE_TIME** → dates (filtered for DOB context)
- **LOCATION** → physical addresses
- **ORGANIZATION** → company/organization names
- **US_DRIVER_LICENSE** → driver's licenses
- **US_PASSPORT** → passport numbers
- **URL** → web URLs
- **IBAN_CODE** → International Bank Account Numbers
- **NRP** → National Registry identifiers
- **MEDICAL_LICENSE** → medical licenses
- **US_BANK_NUMBER** → bank account numbers

#### Custom Entities
- **INDIAN_PHONE_NUMBER** → Indian phone numbers (+91 format)
  - Patterns supported:
    - `+91 9876543210`
    - `+91-9876543210`
    - `91 9876543210`
    - `9876543210`

## Installation

### Required Dependencies

```bash
# Install Presidio packages
pip install presidio-analyzer==2.2.354
pip install presidio-anonymizer==2.2.354

# Install spaCy and download English language model
pip install spacy==3.7.4
python -m spacy download en_core_web_lg
```

All dependencies are included in `requirements.txt`.

## Usage

### Basic Usage

```python
from src.redactors.presidio_redactor import PresidioRedactor

# Initialize redactor
redactor = PresidioRedactor(
    consistency_mode=True,  # Maintain consistent replacements
    seed=42,                # For reproducible fake data
    threshold=0.7           # Confidence threshold (0.0 to 1.0)
)

# Detect PII in text
text = "My name is John Smith and my email is john@example.com"
entities = redactor.detect_pii(text)

# Print detected entities
for entity in entities:
    print(f"{entity.type}: {entity.text} (confidence: {entity.confidence})")

# Redact text
redacted_text, replacements = redactor.redact_text(text)
print(redacted_text)
print(replacements)
```

### Advanced Usage

#### Adjusting Confidence Threshold

```python
# Higher threshold = more precision, fewer detections
redactor.set_threshold(0.9)

# Lower threshold = more recall, more detections
redactor.set_threshold(0.5)
```

#### Getting Statistics

```python
# Get counts of detected PII types
stats = redactor.get_statistics()
print(stats)
# Output: {'person': 2, 'email': 1, 'phone': 1}
```

#### Checking Supported Entities

```python
# Get list of all supported entity types
entities = redactor.get_supported_entities()
print(entities)
```

#### Document Redaction

```python
from docx import Document

# Load document
doc = Document("input.docx")

# Redact entire document
redacted_doc, replacements = redactor.redact_document(doc)

# Save redacted document
redacted_doc.save("redacted_output.docx")
```

### Resetting State

```python
# Clear all cached replacements and detected entities
redactor.reset()
```

## Architecture

### Class Structure

```
BaseRedactor (Abstract)
    ↓
PresidioRedactor
    ├── AnalyzerEngine (Presidio)
    ├── AnonymizerEngine (Presidio)
    ├── FakeDataGenerator (Custom)
    └── IndianPhoneRecognizer (Custom)
```

### Detection Flow

1. **Input Text** → `detect_pii(text)`
2. **Presidio Analysis** → `analyzer.analyze(text)`
3. **Entity Filtering** → Context-based filtering (e.g., DOB vs regular dates)
4. **Entity Mapping** → Map Presidio types to internal types
5. **Confidence Filtering** → Apply threshold
6. **Return Entities** → List of `PIIEntity` objects

### Redaction Flow

1. **Detect PII** → `detect_pii(text)`
2. **Generate Replacements** → `generate_replacement(entity)`
3. **Check Cache** → Use cached replacement if in consistency mode
4. **Apply Replacements** → Replace entities in text
5. **Return Results** → (redacted_text, replacements_dict)

## Custom Recognizers

### Indian Phone Number Recognizer

The `IndianPhoneRecognizer` is a custom pattern-based recognizer that detects Indian phone numbers in various formats:

```python
class IndianPhoneRecognizer(PatternRecognizer):
    def __init__(self):
        patterns = [
            Pattern(
                name="indian_phone_with_plus",
                regex=r"\+91[\s-]?[6-9]\d{9}",
                score=0.85
            ),
            Pattern(
                name="indian_phone_without_plus",
                regex=r"(?:0091|91)?[\s-]?[6-9]\d{9}",
                score=0.75
            ),
        ]
        super().__init__(
            supported_entity="INDIAN_PHONE_NUMBER",
            patterns=patterns,
            name="IndianPhoneRecognizer"
        )
```

### Adding Custom Recognizers

To add more custom recognizers:

1. Create a new class inheriting from `PatternRecognizer`
2. Define regex patterns with confidence scores
3. Add to the registry in `__init__`:

```python
# In PresidioRedactor.__init__
custom_recognizer = MyCustomRecognizer()
registry.add_recognizer(custom_recognizer)
```

## Performance Characteristics

### Speed
- **Slower than RegexRedactor** due to NLP processing
- **Similar to NER models** (spaCy-based)
- Suitable for batch processing, not real-time streaming

### Accuracy
- **High precision** with proper threshold tuning
- **Good recall** for standard PII types
- **Context-aware** detection using NLP

### Resource Usage
- **Memory**: ~500MB (spaCy model + Presidio)
- **CPU**: Moderate (NLP processing)
- **First run**: Slower (model loading)

## Comparison with Other Redactors

| Feature | Regex | Presidio | NER |
|---------|-------|----------|-----|
| Speed | Fast | Moderate | Moderate |
| Accuracy | Good | High | High |
| Context-Aware | No | Yes | Yes |
| Custom Entities | Easy | Moderate | Complex |
| Setup Complexity | Low | Moderate | High |
| Resource Usage | Low | Moderate | High |

## Error Handling

### Import Errors

```python
from src.redactors.presidio_redactor import PRESIDIO_AVAILABLE

if not PRESIDIO_AVAILABLE:
    print("Presidio not installed")
    # Fallback to RegexRedactor
```

### Runtime Errors

The redactor handles errors gracefully:
- Missing spaCy model → Informative error message
- Analysis failures → Returns empty entity list with warning
- Invalid threshold → Raises `ValueError`

## Testing

### Run Tests

```bash
# Run the test script
python test_presidio_redactor.py
```

### Sample Output

```
✅ Presidio is available!
✅ PresidioRedactor initialized successfully!
✅ Detected 10 PII entities:
1. [PERSON] 'John Smith' (confidence: 0.85)
2. [EMAIL] 'john.smith@example.com' (confidence: 0.95)
3. [PHONE] '+1-555-123-4567' (confidence: 0.90)
...
```

## Best Practices

### 1. Threshold Selection
- **0.9+**: High precision, fewer false positives
- **0.7-0.8**: Balanced (recommended)
- **0.5-0.6**: High recall, more false positives

### 2. Consistency Mode
- Enable for documents where same PII appears multiple times
- Ensures "John Smith" always maps to same fake name

### 3. Seed Usage
- Use fixed seed for reproducible testing
- Use random seed (None) for production

### 4. Custom Recognizers
- Add domain-specific recognizers for specialized PII
- Balance regex complexity vs. performance

### 5. Error Handling
- Check `PRESIDIO_AVAILABLE` before instantiation
- Wrap initialization in try-except blocks
- Have fallback strategy (e.g., RegexRedactor)

## Limitations

1. **Language Support**: Primarily English (depends on spaCy model)
2. **Context Sensitivity**: DATE_TIME filtering is heuristic-based
3. **Performance**: Not suitable for real-time, high-throughput scenarios
4. **Model Size**: Requires ~500MB for spaCy model
5. **Ambiguity**: May miss PII in highly contextual or abbreviated forms

## Future Enhancements

- [ ] Multi-language support (additional spaCy models)
- [ ] More custom recognizers (Aadhaar, PAN card, etc.)
- [ ] Configurable entity types (selective detection)
- [ ] Performance optimization (batch processing)
- [ ] Integration with custom NLP models
- [ ] Enhanced context filtering algorithms

## References

- [Presidio Documentation](https://microsoft.github.io/presidio/)
- [spaCy Documentation](https://spacy.io/)
- [Custom Recognizers Guide](https://microsoft.github.io/presidio/analyzer/adding_recognizers/)

## License

This implementation follows the project's license. Presidio is licensed under MIT License.
