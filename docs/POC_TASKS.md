# POC Implementation Tasks

## Overview
We need to implement and test 3 different approaches for PII detection, then create a hybrid approach combining the best of all three.

## Task 1: Regex-Based Redactor
**File**: `src/redactors/regex_redactor.py`

### Requirements:
- Inherit from `BaseRedactor`
- Use patterns from `PIIPatterns` class
- Implement detection for:
  - Emails (high confidence)
  - Phone numbers (multiple formats)
  - SSNs (with validation)
  - Credit cards (with Luhn validation)
  - IP addresses (with validation)
  - DOB (multiple date formats)
  - Basic addresses
- Use `FakeDataGenerator` for replacements
- Handle overlapping matches
- Return confidence scores

### Expected Performance:
- **Precision**: 70-80% (may catch non-PII patterns)
- **Recall**: 60-75% (limited to pattern matching)
- **Speed**: Fast (<1s for 100 pages)

---

## Task 2: NER-Based Redactor (spaCy)
**File**: `src/redactors/ner_redactor.py`

### Requirements:
- Inherit from `BaseRedactor`
- Use spaCy's `en_core_web_lg` model
- Detect entity types:
  - PERSON → names
  - ORG → organizations
  - GPE → locations (for addresses)
  - DATE → dates of birth (with context)
- Post-processing for:
  - Email detection in text
  - Phone number patterns
- Context-aware filtering
- Confidence thresholding

### Expected Performance:
- **Precision**: 75-85% (better context understanding)
- **Recall**: 70-80% (may miss structured PII)
- **Speed**: Medium (3-5s for 100 pages)

---

## Task 3: Presidio-Based Redactor
**File**: `src/redactors/presidio_redactor.py`

### Requirements:
- Inherit from `BaseRedactor`
- Use Presidio Analyzer and Anonymizer
- Configure recognizers for all PII types
- Custom recognizers for:
  - Indian phone numbers
  - Custom date formats
  - Company-specific patterns
- Threshold tuning
- Result aggregation

### Expected Performance:
- **Precision**: 80-90% (purpose-built)
- **Recall**: 75-85% (comprehensive detection)
- **Speed**: Medium-slow (5-8s for 100 pages)

---

## Task 4: Hybrid Redactor
**File**: `src/redactors/hybrid_redactor.py`

### Requirements:
- Combine all three approaches
- Strategy:
  1. Run regex for structured data (high confidence)
  2. Run NER for contextual entities
  3. Run Presidio as validator/fallback
  4. Merge results with deduplication
  5. Resolve conflicts (prioritize by confidence)
- Weighted voting system
- Configurable approach weights

### Expected Performance:
- **Precision**: 85-92% (best combination)
- **Recall**: 85-92% (comprehensive coverage)
- **Speed**: Slowest (8-12s for 100 pages)

---

## Task 5: Test Data Preparation
**Directory**: `tests/test_data/`

### Requirements:
- Split Red Herring Prospectus into 6 parts
- Create ground truth annotations for 2 files
- JSON format with:
  ```json
  [
    {
      "text": "john.doe@example.com",
      "type": "EMAIL",
      "start": 125,
      "end": 145,
      "document": "part_1.docx",
      "paragraph": 5
    }
  ]
  ```
- Cover all PII types
- Include edge cases

---

## Task 6: POC Evaluation Script
**File**: `src/poc_evaluation.py`

### Requirements:
- Test all 4 redactors on test data
- Calculate metrics for each
- Generate comparison report
- Create visualizations:
  - Bar charts (precision/recall comparison)
  - Confusion matrices
  - Per-category breakdowns
- Output to `evaluation/poc_results.md`

### Deliverable:
Comprehensive report recommending which approach (or hybrid) to use.

---

## Success Criteria
- All 4 redactors implemented and functional
- Test data properly annotated
- Evaluation completed with metrics
- Clear recommendation with justification
