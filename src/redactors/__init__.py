"""Redactor implementations for PII detection and redaction"""
from .base_redactor import BaseRedactor, PIIEntity
from .regex_redactor import RegexRedactor

# Import PresidioRedactor with graceful fallback
try:
    from .presidio_redactor import PresidioRedactor
    PRESIDIO_AVAILABLE = True
except ImportError:
    # Presidio dependencies not available
    PRESIDIO_AVAILABLE = False
    PresidioRedactor = None

# Import NERRedactor with graceful fallback
try:
    from .ner_redactor import NERRedactor
    NER_AVAILABLE = True
except ImportError:
    # spaCy or other NER dependencies not available
    NER_AVAILABLE = False
    NERRedactor = None

# Import HybridRedactor (always available, uses what's installed)
from .hybrid_redactor import HybridRedactor

# Build __all__ dynamically
__all__ = ["BaseRedactor", "PIIEntity", "RegexRedactor", "HybridRedactor"]
if PRESIDIO_AVAILABLE:
    __all__.append("PresidioRedactor")
if NER_AVAILABLE:
    __all__.append("NERRedactor")
