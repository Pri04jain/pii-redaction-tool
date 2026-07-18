"""Flask web application for PII Redaction Tool"""
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import sys
import json
from pathlib import Path
import tempfile
import traceback
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.utils.document_handler import DocumentHandler
from src.redactors import RegexRedactor, PresidioRedactor, HybridRedactor

# Try to import NER (may fail)
try:
    from src.redactors import NERRedactor
    NER_AVAILABLE = True
except:
    NER_AVAILABLE = False

app = Flask(__name__, 
           template_folder='../templates',
           static_folder='../static')
app.config.from_object(Config)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure upload and output directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# Log startup information
logger.info(f"Upload folder: {app.config['UPLOAD_FOLDER']}")
logger.info(f"Output folder: {app.config['OUTPUT_FOLDER']}")
logger.info(f"NER Available: {NER_AVAILABLE}")

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
        logger.info("=== Upload request received ===")
        
        # Check if file is present
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return jsonify({'error': 'Invalid file type. Only DOCX files are allowed'}), 400
        
        # Get redaction mode
        mode = request.form.get('mode', 'hybrid')
        logger.info(f"Redaction mode: {mode}")
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file to: {input_path}")
        file.save(input_path)
        
        # Load document
        logger.info("Loading document...")
        doc = DocumentHandler.read_document(input_path)
        logger.info(f"Document loaded successfully: {len(doc.paragraphs)} paragraphs")
        
        # Import appropriate redactor (already imported at top)
        logger.info(f"Initializing {mode} redactor...")
        if mode == "regex":
            redactor = RegexRedactor()
        elif mode == "ner":
            if NER_AVAILABLE:
                redactor = NERRedactor()
            else:
                logger.error("NER mode not available")
                return jsonify({'error': 'NER mode not available. Please use another mode.'}), 400
        elif mode == "presidio":
            redactor = PresidioRedactor()
        else:  # hybrid
            redactor = HybridRedactor()
        
        logger.info(f"Redactor initialized: {type(redactor).__name__}")
        
        # Redact document
        logger.info("Starting redaction...")
        redacted_doc, replacements = redactor.redact_document(doc)
        logger.info(f"Redaction complete: {len(replacements)} replacements made")
        
        # Get statistics
        stats = redactor.get_statistics()
        logger.info(f"Statistics: {stats}")
        
        # Save redacted document
        output_filename = f"redacted_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        logger.info(f"Saving redacted document to: {output_path}")
        DocumentHandler.save_document(redacted_doc, output_path)
        logger.info("Document saved successfully")
        
        # Clean up input file
        os.remove(input_path)
        logger.info("Input file cleaned up")
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'stats': stats,
            'total_redactions': sum(stats.values())
        })
    
    except Exception as e:
        logger.error(f"=== ERROR in upload_file ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full traceback:\n{traceback.format_exc()}")
        
        return jsonify({
            'error': f'{type(e).__name__}: {str(e)}',
            'details': traceback.format_exc()
        }), 500

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
    """Health check endpoint with dependency info"""
    try:
        # Quick basic health check
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'message': 'Server is running'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/health/detailed')
def health_detailed():
    """Detailed health check with dependency info"""
    try:
        import spacy
        spacy_model_loaded = False
        spacy_model_name = None
        spacy_error = None
        
        # Try to check installed models without loading them
        try:
            import spacy.cli
            installed_models = list(spacy.util.get_installed_models())
            logger.info(f"Installed spaCy models: {installed_models}")
            
            # Try loading models
            for model in ['en_core_web_sm', 'en_core_web_md', 'en_core_web_lg']:
                if model in installed_models:
                    try:
                        nlp = spacy.load(model)
                        spacy_model_loaded = True
                        spacy_model_name = model
                        break
                    except Exception as load_error:
                        logger.error(f"Failed to load {model}: {load_error}")
                        spacy_error = str(load_error)
        except Exception as check_error:
            logger.error(f"Error checking models: {check_error}")
            spacy_error = str(check_error)
        
        # Check Presidio
        presidio_available = False
        presidio_error = None
        try:
            from presidio_analyzer import AnalyzerEngine
            presidio_available = True
        except Exception as p_error:
            presidio_error = str(p_error)
        
        return jsonify({
            'status': 'healthy',
            'version': '1.0.0',
            'dependencies': {
                'spacy_available': True,
                'spacy_model_loaded': spacy_model_loaded,
                'spacy_model': spacy_model_name,
                'spacy_error': spacy_error,
                'presidio_available': presidio_available,
                'presidio_error': presidio_error,
                'ner_available': NER_AVAILABLE
            },
            'folders': {
                'upload': str(app.config['UPLOAD_FOLDER']),
                'output': str(app.config['OUTPUT_FOLDER'])
            }
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

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
