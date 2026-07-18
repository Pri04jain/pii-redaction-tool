#!/bin/bash

echo "=== Starting PII Redaction Tool ==="
echo "Python version:"
python --version

echo ""
echo "=== Checking spaCy installation ==="
python -c "import spacy; print(f'spaCy version: {spacy.__version__}')"

echo ""
echo "=== Checking for spaCy models ==="
python -m spacy info en_core_web_lg || echo "en_core_web_lg not found"

echo ""
echo "=== Checking Presidio installation ==="
python -c "from presidio_analyzer import AnalyzerEngine; print('Presidio analyzer: OK')" || echo "Presidio not available"

echo ""
echo "=== Creating directories ==="
mkdir -p uploads output temp
ls -la

echo ""
echo "=== Starting Gunicorn ==="
exec gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 2 --log-level debug src.app:app
