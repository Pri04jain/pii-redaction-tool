"""Flask web application for PII Redaction Tool"""
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
import tempfile
import traceback

from config import Config
from utils.document_handler import DocumentHandler

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
app.config.from_object(Config)
CORS(app)

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and redaction"""
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Only DOCX files are allowed'}), 400
        
        # Get redaction mode
        mode = request.form.get('mode', 'hybrid')
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        # Load document
        doc = DocumentHandler.read_document(input_path)
        
        # Import appropriate redactor
        if mode == "regex":
            from redactors.regex_redactor import RegexRedactor
            redactor = RegexRedactor()
        elif mode == "ner":
            from redactors.ner_redactor import NERRedactor
            redactor = NERRedactor()
        elif mode == "presidio":
            from redactors.presidio_redactor import PresidioRedactor
            redactor = PresidioRedactor()
        else:  # hybrid
            from redactors.hybrid_redactor import HybridRedactor
            redactor = HybridRedactor()
        
        # Redact document
        redacted_doc, replacements = redactor.redact_document(doc)
        
        # Save redacted document
        output_filename = f"redacted_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        DocumentHandler.save_document(redacted_doc, output_path)
        
        # Get statistics
        stats = redactor.get_statistics()
        
        # Clean up input file
        os.remove(input_path)
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'stats': stats,
            'total_redactions': sum(stats.values())
        })
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download redacted file"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        response = send_file(file_path, as_attachment=True)
        
        # Clean up file after sending
        @response.call_on_close
        def cleanup():
            try:
                os.remove(file_path)
            except:
                pass
        
        return response
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'version': '1.0.0'})

@app.route('/api/modes')
def get_modes():
    """Get available redaction modes"""
    return jsonify({
        'modes': [
            {
                'id': 'regex',
                'name': 'Regex-Based',
                'description': 'Fast pattern matching for structured data',
                'speed': 'Fast'
            },
            {
                'id': 'ner',
                'name': 'NER (spaCy)',
                'description': 'Context-aware named entity recognition',
                'speed': 'Medium'
            },
            {
                'id': 'presidio',
                'name': 'Presidio',
                'description': 'Microsoft\'s comprehensive PII detection',
                'speed': 'Medium'
            },
            {
                'id': 'hybrid',
                'name': 'Hybrid (Recommended)',
                'description': 'Best combination of all approaches',
                'speed': 'Slower but most accurate'
            }
        ]
    })

if __name__ == '__main__':
    port = app.config['PORT']
    debug = app.config['DEBUG']
    
    print(f"\n{'='*60}")
    print(f"🚀 PII Redaction Tool Server Starting...")
    print(f"{'='*60}")
    print(f"📍 URL: http://localhost:{port}")
    print(f"🔧 Mode: {'Development' if debug else 'Production'}")
    print(f"{'='*60}\n")
    
    app.run(
        host=app.config['HOST'],
        port=port,
        debug=debug
    )
