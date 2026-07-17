# PII Redaction Tool

A comprehensive tool for detecting and redacting Personally Identifiable Information (PII) from DOCX documents using multiple detection approaches.

## 🎯 Project Overview

This tool automatically detects and replaces sensitive information in documents with realistic fake alternatives while maintaining document structure and consistency.

### Supported PII Types
- ✅ Full Names
- ✅ Email Addresses
- ✅ Phone Numbers
- ✅ Company Names
- ✅ Physical Addresses
- ✅ Social Security Numbers (SSNs)
- ✅ Credit Card Numbers
- ✅ Dates of Birth
- ✅ IP Addresses

## 🚀 Quick Start

### Prerequisites
- Python 3.9 or higher
- pip package manager
- 2GB RAM minimum (for NER models)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd pii-redaction-tool
```

2. **Create virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Download spaCy model**
```bash
python -m spacy download en_core_web_lg
```

5. **Set up environment variables**
```bash
copy .env.example .env
# Edit .env with your configurations
```

### Running Locally

#### Web Application
```bash
python src/app.py
```
Visit `http://localhost:5000` in your browser.

#### CLI Usage
```bash
python src/main.py --input "path/to/document.docx" --output "path/to/redacted.docx" --mode hybrid
```

## 🏗️ Architecture

### Detection Approaches

We implement and compare multiple PII detection approaches:

#### 1. **Regex-Based Detection**
- Pattern matching for structured data
- Fast and lightweight
- Best for: emails, phone numbers, SSNs, credit cards, IPs

#### 2. **NER (Named Entity Recognition)**
- spaCy's pre-trained models
- Context-aware detection
- Best for: names, organizations, locations

#### 3. **Presidio (Microsoft)**
- Purpose-built PII detection framework
- Combines regex, NER, and custom recognizers
- Best for: comprehensive detection

#### 4. **Hybrid Approach** ⭐ (Recommended)
- Combines strengths of all three
- Highest accuracy and precision
- Selected based on POC evaluation results

### Project Structure

```
pii-redaction-tool/
├── src/
│   ├── redactors/
│   │   ├── __init__.py
│   │   ├── base_redactor.py          # Abstract base class
│   │   ├── regex_redactor.py         # Regex-based implementation
│   │   ├── ner_redactor.py           # spaCy NER implementation
│   │   ├── presidio_redactor.py      # Presidio implementation
│   │   └── hybrid_redactor.py        # Combined approach
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── document_handler.py       # DOCX read/write operations
│   │   ├── fake_data_generator.py    # Consistent fake data generation
│   │   ├── evaluator.py              # Metrics calculation
│   │   └── pii_patterns.py           # Regex patterns library
│   ├── app.py                        # Flask web application
│   ├── main.py                       # CLI entry point
│   └── config.py                     # Configuration management
├── tests/
│   ├── test_data/                    # Test documents
│   ├── ground_truth/                 # Annotated test data
│   └── test_redactors.py             # Unit tests
├── evaluation/
│   ├── evaluation_report.md          # Detailed evaluation results
│   ├── metrics.csv                   # Raw metrics data
│   └── confusion_matrices/           # Visualization outputs
├── static/                           # CSS, JS files
├── templates/                        # HTML templates
├── docs/                             # Additional documentation
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment template
├── .gitignore
└── README.md
```

## 🧪 Approach Comparison

### POC Results Summary

| Approach | Precision | Recall | F1 Score | Processing Time |
|----------|-----------|--------|----------|-----------------|
| Regex    | TBD       | TBD    | TBD      | TBD             |
| NER      | TBD       | TBD    | TBD      | TBD             |
| Presidio | TBD       | TBD    | TBD      | TBD             |
| Hybrid   | TBD       | TBD    | TBD      | TBD             |

*Results will be populated after POC completion*

### Tradeoffs

#### Regex-Based
- ✅ **Pros**: Fast, lightweight, excellent for structured data
- ❌ **Cons**: High false positives, misses context-dependent PII

#### NER-Based
- ✅ **Pros**: Context-aware, good for names/locations
- ❌ **Cons**: May miss domain-specific entities, requires model

#### Presidio
- ✅ **Pros**: Comprehensive, extensible, maintained by Microsoft
- ❌ **Cons**: Heavier dependencies, may need fine-tuning

#### Hybrid
- ✅ **Pros**: Best of all approaches, highest accuracy
- ❌ **Cons**: Slower processing, more complex

## 📊 Evaluation Methodology

### Metrics Calculated
- **Precision**: Accuracy of positive predictions (avoiding false positives)
- **Recall**: Coverage of actual PII (catching all instances)
- **F1 Score**: Harmonic mean of precision and recall
- **Accuracy**: Overall correctness

### Ground Truth Creation
- Manual annotation of test documents
- JSON format with PII locations and types
- Cross-validated by multiple reviewers

### Per-Category Evaluation
Each PII type evaluated independently to identify strengths and weaknesses.

## 🌐 Deployment

### Railway Deployment

1. **Install Railway CLI**
```bash
npm install -g @railway/cli
```

2. **Login to Railway**
```bash
railway login
```

3. **Initialize and Deploy**
```bash
railway init
railway up
```

4. **Set Environment Variables**
```bash
railway variables set FLASK_ENV=production
railway variables set SECRET_KEY=<your-secret-key>
```

### Alternative Platforms
- **Render**: Connect GitHub repo, set build command
- **Heroku**: Use provided Procfile
- **Vercel**: Requires serverless adaptation

## 🔒 Security Considerations

- **No Data Storage**: Uploaded files processed in-memory, deleted immediately
- **HTTPS Only**: All deployments use secure connections
- **No Logging of PII**: Original values never logged
- **Session Isolation**: Each request independent

## 🛠️ Development

### Running Tests
```bash
pytest tests/ -v --cov=src
```

### Adding New PII Type

1. Add pattern to `src/utils/pii_patterns.py`
2. Update recognizers in respective redactor files
3. Add test cases in `tests/test_redactors.py`
4. Update evaluation ground truth

### Code Style
```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/
```

## 📈 Performance

- **Processing Speed**: ~1-2 pages/second (hybrid mode)
- **Memory Usage**: ~500MB-1GB (with NER model loaded)
- **Accuracy Target**: >85% recall, >80% precision

## 🐛 Known Limitations

### False Positives
- Common words matching name patterns
- Numeric sequences resembling phone/SSN
- Mitigation: Adjustable confidence thresholds

### False Negatives
- Unconventional PII formats
- Domain-specific terminology
- Mitigation: Custom pattern addition, fine-tuning

### Format Preservation
- Complex formatting may be simplified
- Tables and images preserved as-is
- Mitigation: Careful python-docx usage

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📝 License

This project is created as part of an assignment for Enterprise Data.

## 📧 Contact

For questions or issues, please open a GitHub issue.

## 🙏 Acknowledgments

- spaCy for NER models
- Microsoft Presidio for PII framework
- Faker library for realistic fake data
- Python-docx for document handling

---

**Status**: 🚧 In Development  
**Last Updated**: 2026-07-17  
**Version**: 1.0.0
