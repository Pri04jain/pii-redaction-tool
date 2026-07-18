"""Utility to load spaCy models with automatic download fallback"""
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)


def load_spacy_model(model_name='en_core_web_sm'):
    """
    Load a spaCy model, downloading it if necessary
    
    Args:
        model_name: Name of the spaCy model to load
    
    Returns:
        Loaded spaCy model or None if failed
    """
    import spacy
    
    # Try to load the model
    try:
        logger.info(f"Attempting to load spaCy model: {model_name}")
        nlp = spacy.load(model_name)
        logger.info(f"✅ Successfully loaded spaCy model: {model_name}")
        return nlp
    except OSError:
        logger.warning(f"Model {model_name} not found. Attempting to download...")
        
        # Try to download it
        try:
            logger.info(f"Downloading {model_name}...")
            subprocess.check_call(
                [sys.executable, "-m", "spacy", "download", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"✅ Downloaded {model_name}")
            
            # Try loading again
            nlp = spacy.load(model_name)
            logger.info(f"✅ Successfully loaded {model_name} after download")
            return nlp
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download {model_name}: {e}")
        except Exception as e:
            logger.error(f"❌ Error loading {model_name}: {e}")
    
    return None


def get_available_spacy_model():
    """
    Get any available spaCy model, trying multiple options
    
    Returns:
        Loaded spaCy model or None
    """
    models_to_try = [
        'en_core_web_sm',  # Smallest, fastest
        'en_core_web_md',  # Medium
        'en_core_web_lg',  # Largest, most accurate
    ]
    
    for model_name in models_to_try:
        logger.info(f"Trying to load: {model_name}")
        nlp = load_spacy_model(model_name)
        if nlp:
            return nlp
    
    logger.error("❌ No spaCy model could be loaded")
    return None


# Cache for loaded model
_cached_model = None


def get_cached_spacy_model():
    """
    Get a cached spaCy model, loading it on first call
    
    Returns:
        Loaded spaCy model or None
    """
    global _cached_model
    
    if _cached_model is None:
        logger.info("Loading spaCy model for the first time...")
        _cached_model = get_available_spacy_model()
    
    return _cached_model
