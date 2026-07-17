# Regex-Based PII Redactor Implementation

## Overview
The `RegexRedactor` class provides fast, pattern-based PII detection and redaction with high precision for structured data formats.

## Location
`src/redactors/regex_redactor.py`

## Features

### 1. PII Detection Coverage
The implementation detects the following PII types:

| PII Type | Patterns Supported | Confidence | Validation |
|----------|-------------------|------------|------------|
| **Email** | Standard email format | 0.95 | Format validation |
| **Phone** | International (+91, +1), US formats | 0.80-0.90 | Digit count (min 10) |
| **SSN** | XXX-XX-XXXX, XXX XX XXXX, XXXXXXXXX | 0.70-0.85 | ✓ Format & sequential check |
| **Credit Card** | 15-16 digits with/without separators | 0.95 | ✓ Luhn algorithm |
| **IP Address** | IPv4 format | 0.60-0.80 | ✓ Range validation (0-255) |
| **Date of Birth** | MM/DD/YYYY, Month DD, YYYY | 0.70-0.75 | Format validation |
| **Address** | Street addresses, PO Boxes | 0.75-0.85 | Pattern matching |

### 2. Validation Logic (False Positive Reduction)

#### SSN Validation (`PIIPatterns.validate_ssn`)
- Checks for 9 digits
- Rejects all zeros (000000000)
- Rejects sequential patterns (123456789)
- Format validation for dashes/spaces

#### Credit Card Validation (`PIIPatterns.validate_credit_card`)
- Luhn algorithm checksum validation
- Only valid credit card numbers are detected
- Reduces false positives significantly

#### IP Address Validation (`PIIPatterns.validate_ip_address`)
- Validates each octet is 0-255
- Rejects malformed IP addresses
- Lower confidence for private IPs (192.168.x.x, 10.x.x.x)

### 3. Overlap Resolution
The `_resolve_overlaps()` method handles overlapping matches by:
- Choosing the longest match when overlaps occur
- Maintaining consistent entity positions
- Preventing duplicate detections

### 4. Consistency Mode
When enabled (default):
- Same PII value always gets same replacement
- Uses hash-based deterministic generation
- Maintains replacement cache across multiple calls

### 5. Fake Data Generation
Uses `FakeDataGenerator` for realistic replacements:
- Emails: Fake email addresses
- Phones: Format-matching phone numbers (preserves +91, +1 prefixes)
- SSNs: Valid format SSNs
- Credit Cards: Masked format (XXXX-XXXX-XXXX-1234)
- IPs: Private IP addresses
- DOBs: Format-matching dates
- Addresses: Complete fake addresses

## Usage Examples

### Basic Usage
```python
from src.redactors.regex_redactor import RegexRedactor

# Initialize redactor
redactor = RegexRedactor(consistency_mode=True, seed=42)

# Detect PII in text
text = "Email: john@example.com, Phone: +91 9876543210"
entities = redactor.detect_pii(text)

for entity in entities:
    print(f"{entity.type}: {entity.text} (confidence: {entity.confidence})")
```

### Redact Text
```python
# Redact PII and get replacements
redacted_text, replacements = redactor.redact_text(text)

print(f"Original: {text}")
print(f"Redacted: {redacted_text}")
print(f"Replacements: {replacements}")
```

### Get Statistics
```python
# Get PII type counts
stats = redactor.get_statistics()
print(f"Detected: {stats}")
# Output: {'email': 1, 'phone': 1}
```

### Reset State
```python
# Clear detected entities and replacement cache
redactor.reset()
```

## Performance Characteristics

### Strengths
- ✓ Fast processing (compiled regex patterns)
- ✓ High precision for structured data
- ✓ Low false positive rate (validation reduces FPs)
- ✓ Consistent replacements across documents
- ✓ No external API calls required
- ✓ Deterministic output (with seed)

### Limitations
- ✗ May miss context-dependent PII (e.g., names without clear markers)
- ✗ Address patterns can be greedy (occasional false positives)
- ✗ Doesn't understand semantic context
- ✗ Fixed pattern set (not adaptive)

## Confidence Scores

Confidence scores indicate detection reliability:

- **0.95**: Email (well-formed), Credit Card (Luhn validated)
- **0.90**: International phone (+91, +1 prefix)
- **0.85**: SSN (with dashes), PO Box addresses
- **0.80**: Phone (standard format), Public IP addresses
- **0.75**: Street addresses, Spelled-out DOB
- **0.70**: Numeric DOB, SSN (no dashes)
- **0.60**: Private IP addresses

Lower confidence may indicate potential false positives.

## Testing

### Test Files Created
1. `test_regex_redactor.py` - Basic functionality test
2. `test_validation.py` - Validation function tests
3. `test_comprehensive.py` - Comprehensive PII detection test

### Running Tests
```bash
python test_regex_redactor.py
python test_validation.py
python test_comprehensive.py
```

## Integration

The `RegexRedactor` is exported from `src/redactors/__init__.py`:

```python
from src.redactors import RegexRedactor

# Use in your application
redactor = RegexRedactor()
```

## Architecture

```
RegexRedactor (inherits from BaseRedactor)
├── PIIPatterns (regex patterns & validation)
├── FakeDataGenerator (replacement generation)
└── PIIEntity (detection result data structure)
```

## Configuration Options

```python
RegexRedactor(
    consistency_mode=True,  # Maintain consistent replacements
    seed=42                 # Seed for reproducible fake data
)
```

## Future Enhancements

Potential improvements:
1. Custom pattern injection
2. Context-aware validation
3. Configurable confidence thresholds
4. Performance metrics tracking
5. Multi-language support
6. Custom replacement templates

## Test Results Summary

**Comprehensive Test (17 PII entities detected):**
- Emails: 3 (17.6%)
- Phones: 3 (17.6%)
- IP Addresses: 3 (17.6%)
- Addresses: 4 (23.5%)
- DOB: 2 (11.8%)
- SSN: 1 (5.9%)
- Credit Card: 1 (5.9%)

**Validation Effectiveness:**
- Invalid SSN (123-45-6789): Correctly rejected ✓
- Invalid Credit Card (4532-1488-0343-6467): Correctly rejected ✓
- Valid Credit Card (4532015112830366): Correctly detected ✓

**Consistency:**
- Same email detected twice: Same replacement used ✓

## Conclusion

The `RegexRedactor` implementation provides a robust, fast solution for structured PII detection with validation-based false positive reduction. It's ideal for documents with clearly formatted PII and offers consistent, deterministic redaction behavior.
