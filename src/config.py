"""Configuration management for PII Redaction Tool"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent.parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
OUTPUT_FOLDER = BASE_DIR / "output"
TEMP_FOLDER = BASE_DIR / "temp"

# Create directories if they don't exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
TEMP_FOLDER.mkdir(exist_ok=True)

# Flask Configuration
class Config:
    """Flask application configuration"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_FILE_SIZE", 52428800))  # 50MB default
    UPLOAD_FOLDER = UPLOAD_FOLDER
    OUTPUT_FOLDER = OUTPUT_FOLDER
    ALLOWED_EXTENSIONS = {"docx"}
    
    # Model Configuration
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_lg")
    USE_GPU = os.getenv("USE_GPU", "false").lower() == "true"
    
    # Redaction Configuration
    REDACTION_MODE = os.getenv("REDACTION_MODE", "hybrid")
    CONSISTENCY_MODE = os.getenv("CONSISTENCY_MODE", "true").lower() == "true"
    
    # Deployment
    PORT = int(os.getenv("PORT", 5000))
    HOST = os.getenv("HOST", "0.0.0.0")
    DEBUG = os.getenv("FLASK_ENV", "development") == "development"

# PII Categories
PII_CATEGORIES = [
    "PERSON",
    "EMAIL",
    "PHONE",
    "SSN",
    "CREDIT_CARD",
    "IP_ADDRESS",
    "ADDRESS",
    "DATE_OF_BIRTH",
    "ORGANIZATION"
]

# Evaluation thresholds
EVALUATION_CONFIG = {
    "min_recall": 0.85,
    "min_precision": 0.80,
    "min_f1": 0.82
}
