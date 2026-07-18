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

# Pre-initialize redactors to avoid timeout on first request
logger.info("Pre-initializing redactors...")
_redactors_cache = {}

def get_redactor(mode):
    """Get or create a redactor instance (cached)"""
    if mode not in _redactors_cache:
        logger.info(f"Creating new {mode} redactor...")
        try:
            if mode == "regex":
                _redactors_cache[mode] = RegexRedactor()
            elif mode == "ner":
                if NER_AVAILABLE:
                    _redactors_cache[mode] = NERRedactor()
                else:
                    logger.warning("NER not available")
                    return None
            elif mode == "presidio":
                logger.info("Initializing Presidio (this may take a moment)...")
                _redactors_cache[mode] = PresidioRedactor()
            elif mode == "hybrid":
                logger.info("Initializing Hybrid (this may take a moment)...")
                _redactors_cache[mode] = HybridRedactor()
            logger.info(f"✅ {mode} redactor created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create {mode} redactor: {e}")
            logger.error(traceback.format_exc())
            # Don't cache failed attempts
            return None
    else:
        logger.info(f"Using cached {mode} redactor")
    
    return _redactors_cache.get(mode)

# Pre-load regex redactor (fast, always works)
try:
    logger.info("Pre-loading regex redactor...")
    get_redactor("regex")
    logger.info("✅ Regex redactor ready")
except Exception as e:
    logger.error(f"Failed to pre-load regex redactor: {e}")

# Try to pre-load presidio (may be slow, skip for faster startup)
# Presidio will be loaded on first use
# try:
#     logger.info("Pre-loading presidio redactor...")
#     get_redactor("presidio")
#     logger.info("✅ Presidio redactor ready")
# except Exception as e:
#     logger.warning(f"Presidio pre-load failed: {e}")
#     logger.warning("Presidio will be loaded on first use")
logger.info("Presidio will be loaded on first use (lazy loading enabled)")

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
    import time
    start_time = time.time()
    
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
        mode = request.form.get('mode', 'regex')
        logger.info(f"Redaction mode: {mode}")
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.info(f"Saving file to: {input_path}")
        file.save(input_path)
        file_save_time = time.time()
        
        # Load document
        logger.info("Loading document...")
        doc = DocumentHandler.read_document(input_path)
        logger.info(f"Document loaded successfully: {len(doc.paragraphs)} paragraphs")
        doc_load_time = time.time()
        
        # Get cached redactor (or create if not cached)
        logger.info(f"Getting {mode} redactor...")
        redactor = get_redactor(mode)
        
        if redactor is None:
            error_msg = f'{mode.upper()} mode is not available or failed to initialize.'
            
            # Provide specific guidance based on mode
            if mode == "presidio" or mode == "hybrid":
                error_msg += ' This may be due to spaCy model not being available. Try using Regex mode instead.'
            
            logger.error(error_msg)
            logger.error(f"Available redactors: {list(_redactors_cache.keys())}")
            
            # Clean up uploaded file
            if os.path.exists(input_path):
                os.remove(input_path)
            
            return jsonify({
                'error': error_msg,
                'available_modes': ['regex'] + list(_redactors_cache.keys()),
                'suggestion': 'Try using Regex mode for fast and reliable redaction.'
            }), 400
        
        logger.info(f"Using redactor: {type(redactor).__name__}")
        redactor_init_time = time.time()
        
        # Reset redactor state before use (in case it's cached)
        try:
            redactor.reset()
        except Exception as reset_error:
            logger.warning(f"Redactor reset failed: {reset_error}")
        
        # Redact document
        logger.info("Starting redaction...")
        redaction_start = time.time()
        redacted_doc, replacements = redactor.redact_document(doc)
        redaction_end = time.time()
        logger.info(f"Redaction complete: {len(replacements)} replacements made")
        logger.info(f"Redaction took: {redaction_end - redaction_start:.2f} seconds")
        
        # Get statistics
        stats = redactor.get_statistics()
        logger.info(f"Statistics: {stats}")
        
        # Save redacted document
        output_filename = f"redacted_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        logger.info(f"Saving redacted document to: {output_path}")
        DocumentHandler.save_document(redacted_doc, output_path)
        logger.info("Document saved successfully")
        save_time = time.time()
        
        # Clean up input file
        os.remove(input_path)
        logger.info("Input file cleaned up")
        
        # Calculate total time
        end_time = time.time()
        total_time = end_time - start_time
        processing_time = redaction_end - redaction_start
        
        logger.info(f"=== Total processing time: {total_time:.2f} seconds ===")
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'stats': stats,
            'total_redactions': sum(stats.values()),
            'timing': {
                'total': round(total_time, 2),
                'redaction': round(processing_time, 2),
                'file_load': round(doc_load_time - file_save_time, 2),
                'save': round(save_time - redaction_end, 2)
            },
            'mode': mode
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
        installed_models = []
        
        # Try to get installed models
        try:
            installed_models = list(spacy.util.get_installed_models())
            logger.info(f"Installed spaCy models: {installed_models}")
        except Exception as e:
            logger.error(f"Error getting installed models: {e}")
        
        # Try using the spacy_loader utility
        try:
            from src.utils.spacy_loader import get_cached_spacy_model
            nlp = get_cached_spacy_model()
            
            if nlp:
                spacy_model_loaded = True
                spacy_model_name = nlp.meta.get('name', 'unknown')
                logger.info(f"✅ Loaded model via spacy_loader: {spacy_model_name}")
            else:
                spacy_error = "No model could be loaded"
        except Exception as load_error:
            logger.error(f"spacy_loader failed: {load_error}")
            spacy_error = str(load_error)
        
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
                'spacy_installed_models': installed_models,
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
    """Get available redaction modes with their actual availability status"""
    modes = []
    
    # Check which redactors are actually loaded
    loaded_modes = list(_redactors_cache.keys())
    
    # Regex - always available
    modes.append({
        'id': 'regex',
        'name': 'Regex (Recommended)',
        'description': 'Fast pattern matching for structured data',
        'speed': 'Fast',
        'available': True,
        'status': 'ready'
    })
    
    # Try to load Presidio if not cached
    presidio_available = 'presidio' in loaded_modes
    presidio_status = 'ready' if presidio_available else 'not loaded'
    
    if not presidio_available:
        try:
            test_redactor = get_redactor('presidio')
            presidio_available = test_redactor is not None
            presidio_status = 'ready' if presidio_available else 'failed'
        except:
            presidio_status = 'error'
    
    modes.append({
        'id': 'presidio',
        'name': 'Presidio',
        'description': 'Microsoft\'s comprehensive PII detection',
        'speed': 'Medium',
        'available': presidio_available,
        'status': presidio_status
    })
    
    # Hybrid depends on Presidio
    hybrid_available = presidio_available
    hybrid_status = 'ready' if hybrid_available else 'requires presidio'
    
    modes.append({
        'id': 'hybrid',
        'name': 'Hybrid',
        'description': 'Best combination of all approaches',
        'speed': 'Slower but most accurate',
        'available': hybrid_available,
        'status': hybrid_status
    })
    
    # NER
    ner_available = NER_AVAILABLE and 'ner' in loaded_modes
    ner_status = 'ready' if ner_available else 'not available'
    
    modes.append({
        'id': 'ner',
        'name': 'NER (spaCy)',
        'description': 'Context-aware named entity recognition',
        'speed': 'Medium',
        'available': ner_available,
        'status': ner_status
    })
    
    return jsonify({
        'modes': modes,
        'loaded_redactors': loaded_modes,
        'recommendations': 'Use Regex for fast and reliable redaction. Presidio/Hybrid provide better accuracy but may not be available in all environments.'
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
