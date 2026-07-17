"""Presidio-based PII redactor implementation"""
from typing import List, Dict
from .base_redactor import BaseRedactor, PIIEntity
from ..utils.fake_data_generator import FakeDataGenerator

try:
    from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, Pattern, PatternRecognizer
    from presidio_analyzer.nlp_engine import SpacyNlpEngine
    from presidio_anonymizer import AnonymizerEngine
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    AnalyzerEngine = None
    AnonymizerEngine = None
    RecognizerRegistry = None
    Pattern = None
    PatternRecognizer = None


# Only define IndianPhoneRecognizer if Presidio is available
if PRESIDIO_AVAILABLE:
    class IndianPhoneRecognizer(PatternRecognizer):
        """Custom recognizer for Indian phone numbers"""
        
        def __init__(self):
            patterns = [
                Pattern(
                    name="indian_phone_with_plus",
                    regex=r"\+91[\s-]?[6-9]\d{9}",
                    score=0.85
                ),
                Pattern(
                    name="indian_phone_without_plus",
                    regex=r"(?:0091|91)?[\s-]?[6-9]\d{9}",
                    score=0.75
                ),
            ]
            super().__init__(
                supported_entity="INDIAN_PHONE_NUMBER",
                patterns=patterns,
                name="IndianPhoneRecognizer"
            )
else:
    # Placeholder when Presidio is not available
    IndianPhoneRecognizer = None


class PresidioRedactor(BaseRedactor):
    """
    Presidio-based PII redactor using Microsoft's Presidio framework.
    
    Features:
    - Comprehensive PII detection using pre-trained models
    - Support for standard entities (PERSON, EMAIL, PHONE, SSN, etc.)
    - Custom recognizers for Indian phone numbers
    - Configurable confidence threshold
    - High accuracy with slower performance compared to regex
    """
    
    # Entity type mapping: Presidio -> Internal
    ENTITY_TYPE_MAPPING = {
        "PERSON": "person",
        "EMAIL_ADDRESS": "email",
        "PHONE_NUMBER": "phone",
        "INDIAN_PHONE_NUMBER": "phone",
        "US_SSN": "ssn",
        "CREDIT_CARD": "credit_card",
        "IP_ADDRESS": "ip_address",
        "DATE_TIME": "dob",
        "LOCATION": "address",
        "ORGANIZATION": "organization",
        "US_DRIVER_LICENSE": "driver_license",
        "US_PASSPORT": "passport",
        "URL": "url",
        "IBAN_CODE": "iban",
        "NRP": "national_id",  # National Registry of Persons
        "MEDICAL_LICENSE": "medical_license",
        "US_BANK_NUMBER": "bank_account",
    }
    
    def __init__(self, consistency_mode: bool = True, seed: int = None, threshold: float = 0.7):
        """
        Initialize Presidio redactor
        
        Args:
            consistency_mode: If True, maintain consistent replacements for same values
            seed: Random seed for reproducible fake data generation
            threshold: Minimum confidence score for entity detection (0.0 to 1.0)
        
        Raises:
            ImportError: If Presidio is not installed
        """
        super().__init__(consistency_mode)
        
        if not PRESIDIO_AVAILABLE:
            raise ImportError(
                "Presidio is not installed. Please install it using:\n"
                "pip install presidio-analyzer presidio-anonymizer\n"
                "Also ensure spaCy model is installed:\n"
                "python -m spacy download en_core_web_lg"
            )
        
        self.fake_generator = FakeDataGenerator(seed)
        self.threshold = threshold
        
        # Initialize Presidio engines
        try:
            # Create registry and add custom recognizers
            registry = RecognizerRegistry()
            registry.load_predefined_recognizers()
            
            # Add custom Indian phone number recognizer
            indian_phone_recognizer = IndianPhoneRecognizer()
            registry.add_recognizer(indian_phone_recognizer)
            
            # Initialize analyzer with custom registry
            self.analyzer = AnalyzerEngine(registry=registry)
            self.anonymizer = AnonymizerEngine()
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Presidio engines: {e}\n"
                "Make sure spaCy model is installed:\n"
                "python -m spacy download en_core_web_lg"
            )
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII in text using Presidio analyzer
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of detected PII entities with confidence scores
        """
        entities = []
        
        try:
            # Analyze text with Presidio
            analyzer_results = self.analyzer.analyze(
                text=text,
                language='en',
                score_threshold=self.threshold
            )
            
            # Convert Presidio results to our PIIEntity format
            for result in analyzer_results:
                # Extract the actual text
                entity_text = text[result.start:result.end]
                
                # Map Presidio entity type to our internal type
                entity_type = self.ENTITY_TYPE_MAPPING.get(
                    result.entity_type,
                    result.entity_type.lower()
                )
                
                # Filter DATE_TIME entities that look like DOB
                # Only include dates that might be DOB (context-based filtering)
                if result.entity_type == "DATE_TIME":
                    if not self._is_likely_dob(entity_text, text, result.start, result.end):
                        continue  # Skip non-DOB dates
                
                entities.append(PIIEntity(
                    text=entity_text,
                    type=entity_type,
                    start=result.start,
                    end=result.end,
                    confidence=result.score
                ))
            
            # Sort by start position for consistent ordering
            entities = sorted(entities, key=lambda e: e.start)
            
            # Store detected entities
            self.detected_entities = entities
            
        except Exception as e:
            # Log error but don't fail completely
            print(f"Warning: Presidio detection failed: {e}")
            entities = []
        
        return entities
    
    def _is_likely_dob(self, date_text: str, full_text: str, start: int, end: int) -> bool:
        """
        Heuristic to determine if a date is likely a date of birth
        
        Args:
            date_text: The extracted date text
            full_text: The full text being analyzed
            start: Start position of the date
            end: End position of the date
        
        Returns:
            True if the date is likely a DOB, False otherwise
        """
        # Context window: 50 characters before and after
        context_start = max(0, start - 50)
        context_end = min(len(full_text), end + 50)
        context = full_text[context_start:context_end].lower()
        
        # Keywords that suggest DOB
        dob_keywords = [
            'birth', 'born', 'dob', 'd.o.b', 'date of birth',
            'birthday', 'age', 'born on'
        ]
        
        # Check if any DOB keyword is in the context
        for keyword in dob_keywords:
            if keyword in context:
                return True
        
        # If no specific context, be conservative
        # Only include if it looks like a reasonable birth year (1900-2010)
        import re
        year_match = re.search(r'\b(19\d{2}|20[0-1]\d)\b', date_text)
        if year_match:
            year = int(year_match.group(1))
            if 1900 <= year <= 2010:
                return True
        
        return False
    
    def generate_replacement(self, entity: PIIEntity) -> str:
        """
        Generate fake replacement for PII entity using FakeDataGenerator
        
        Args:
            entity: PIIEntity to replace
        
        Returns:
            Fake replacement value matching the entity type
        """
        original = entity.text
        entity_type = entity.type
        
        # Generate replacement based on entity type
        if entity_type == "person":
            return self.fake_generator.generate_name(original)
        
        elif entity_type == "email":
            return self.fake_generator.generate_email(original)
        
        elif entity_type == "phone":
            return self.fake_generator.generate_phone(original)
        
        elif entity_type == "ssn":
            return self.fake_generator.generate_ssn(original)
        
        elif entity_type == "credit_card":
            return self.fake_generator.generate_credit_card(original)
        
        elif entity_type == "ip_address":
            return self.fake_generator.generate_ip_address(original)
        
        elif entity_type == "dob":
            return self.fake_generator.generate_dob(original)
        
        elif entity_type == "address":
            return self.fake_generator.generate_address(original)
        
        elif entity_type == "organization":
            return self.fake_generator.generate_company(original)
        
        elif entity_type == "driver_license":
            # Generate fake driver license
            return self._get_or_generate_generic(original, "DL", 8)
        
        elif entity_type == "passport":
            # Generate fake passport number
            return self._get_or_generate_generic(original, "P", 9)
        
        elif entity_type == "url":
            # Redact URL but keep domain structure
            return f"https://example-{abs(hash(original)) % 1000}.com"
        
        elif entity_type == "iban":
            # Generate fake IBAN
            return self._get_or_generate_generic(original, "IBAN", len(original))
        
        elif entity_type == "national_id":
            # Generate fake national ID
            return self._get_or_generate_generic(original, "NID", 10)
        
        elif entity_type == "medical_license":
            # Generate fake medical license
            return self._get_or_generate_generic(original, "ML", 8)
        
        elif entity_type == "bank_account":
            # Generate fake bank account
            return self._get_or_generate_generic(original, "BA", 12)
        
        else:
            # Fallback: redact with generic placeholder
            return f"[REDACTED_{entity_type.upper()}]"
    
    def _get_or_generate_generic(self, original: str, prefix: str, length: int) -> str:
        """
        Generate a generic fake identifier
        
        Args:
            original: Original value
            prefix: Prefix for the fake identifier
            length: Length of the numeric part
        
        Returns:
            Fake identifier string
        """
        # Use hash of original for deterministic generation
        import hashlib
        hash_int = int(hashlib.md5(original.encode()).hexdigest(), 16)
        
        # Generate numeric part
        numeric_part = str(hash_int)[:length].zfill(length)
        
        return f"{prefix}{numeric_part}"
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about detected PII
        
        Returns:
            Dictionary with counts of each PII type
        """
        stats = {}
        for entity in self.detected_entities:
            stats[entity.type] = stats.get(entity.type, 0) + 1
        return stats
    
    def reset(self):
        """Reset the redactor state and clear caches"""
        super().reset()
        self.fake_generator.clear_cache()
    
    def set_threshold(self, threshold: float):
        """
        Update the confidence threshold for detection
        
        Args:
            threshold: New threshold value (0.0 to 1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")
        self.threshold = threshold
    
    def get_supported_entities(self) -> List[str]:
        """
        Get list of all supported entity types
        
        Returns:
            List of supported entity type names
        """
        if not PRESIDIO_AVAILABLE or not hasattr(self, 'analyzer'):
            return []
        
        try:
            # Get all supported entities from the analyzer
            recognizers = self.analyzer.registry.recognizers
            entities = set()
            
            for recognizer in recognizers:
                entities.update(recognizer.supported_entities)
            
            return sorted(list(entities))
        except Exception:
            return list(self.ENTITY_TYPE_MAPPING.keys())
