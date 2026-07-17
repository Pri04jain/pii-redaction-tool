"""NER-Based PII Redactor using spaCy"""
import re
from typing import List, Dict, Set
from .base_redactor import BaseRedactor, PIIEntity
from ..utils.fake_data_generator import FakeDataGenerator
from ..utils.pii_patterns import PIIPatterns

# Try to import spaCy
try:
    import spacy
    from spacy.tokens import Doc
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None
    Doc = None


class NERRedactor(BaseRedactor):
    """
    NER-based PII Redactor using spaCy for context-aware detection.
    
    This redactor uses spaCy's Named Entity Recognition to identify PII entities
    with better context awareness than pure regex approaches. It combines NER
    with regex patterns for comprehensive coverage.
    
    Features:
    - Context-aware entity detection (PERSON, ORG, GPE, DATE)
    - Confidence-based filtering (threshold: 0.7)
    - False positive filtering for common words
    - Hybrid approach with regex for emails and phones
    - Consistent fake data generation
    """
    
    # Common words that shouldn't be redacted as PERSON
    COMMON_WORD_BLACKLIST: Set[str] = {
        'Order', 'Ticket', 'Invoice', 'Payment', 'Account', 'Service',
        'Customer', 'Client', 'User', 'Admin', 'Manager', 'Director',
        'January', 'February', 'March', 'April', 'May', 'June', 'July',
        'August', 'September', 'October', 'November', 'December',
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'Support', 'Team', 'Department', 'Company', 'Business', 'Enterprise',
        'Dear', 'Sir', 'Madam', 'Mr', 'Mrs', 'Ms', 'Dr', 'Prof'
    }
    
    # Context words that indicate a DATE is likely a DOB
    DOB_CONTEXT_WORDS: Set[str] = {
        'birth', 'born', 'dob', 'd.o.b', 'birthday', 'age', 'years old'
    }
    
    def __init__(self, consistency_mode: bool = True, confidence_threshold: float = 0.7, seed: int = None):
        """
        Initialize NER Redactor
        
        Args:
            consistency_mode: If True, maintain consistent replacements for same values
            confidence_threshold: Minimum confidence score for entity detection (default: 0.7)
            seed: Random seed for reproducible fake data generation (optional)
        
        Raises:
            ImportError: If spaCy is not installed
            OSError: If the en_core_web_lg model is not installed
        """
        super().__init__(consistency_mode)
        
        if not SPACY_AVAILABLE:
            raise ImportError(
                "spaCy is not installed. Install it with: pip install spacy"
            )
        
        self.confidence_threshold = confidence_threshold
        self.fake_generator = FakeDataGenerator(seed)
        
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_lg")
        except OSError:
            raise OSError(
                "spaCy model 'en_core_web_lg' not found. "
                "Download it with: python -m spacy download en_core_web_lg"
            )
        
        # Compile regex patterns for hybrid approach
        self.patterns = PIIPatterns.compile_patterns()
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII in text using NER and regex patterns
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of detected PII entities with confidence scores
        """
        entities = []
        detected_spans = set()  # Track detected spans to avoid duplicates
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract named entities
        for ent in doc.ents:
            # Filter by confidence threshold
            if hasattr(ent, 'score') and ent.score is not None:
                confidence = ent.score
            else:
                # spaCy doesn't always provide scores, use rule-based confidence
                confidence = self._calculate_confidence(ent, text)
            
            if confidence < self.confidence_threshold:
                continue
            
            # Map spaCy entity types to PII types
            pii_type = self._map_entity_type(ent.label_, ent.text, text, ent.start_char)
            
            if pii_type:
                # Apply false positive filtering
                if self._is_false_positive(ent.text, pii_type, text, ent.start_char):
                    continue
                
                entity = PIIEntity(
                    text=ent.text,
                    type=pii_type,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=confidence
                )
                entities.append(entity)
                detected_spans.add((ent.start_char, ent.end_char))
        
        # Add regex-based detections for emails and phones (hybrid approach)
        entities.extend(self._detect_emails(text, detected_spans))
        entities.extend(self._detect_phones(text, detected_spans))
        
        # DON'T store here - let base class accumulate
        # self.detected_entities will be populated by base_redactor.redact_document()
        
        # Remove overlapping entities (keep higher confidence)
        entities = self._remove_overlaps(entities)
        
        return entities
    
    def _map_entity_type(self, spacy_label: str, text: str, full_text: str, start: int) -> str:
        """
        Map spaCy entity labels to PII types
        
        Args:
            spacy_label: spaCy entity label (PERSON, ORG, etc.)
            text: Entity text
            full_text: Complete text for context
            start: Start position of entity
        
        Returns:
            PII type string or None if not relevant
        """
        label_map = {
            'PERSON': 'person',  # Changed from 'name' to match Presidio
            'ORG': 'organization',
            'GPE': 'location',  # Geopolitical entity (cities, countries)
            'DATE': 'dob',  # Will be filtered by context
            'LOC': 'location',
            'FAC': 'location',  # Facilities
        }
        
        if spacy_label in label_map:
            pii_type = label_map[spacy_label]
            
            # Special handling for DATE - only flag if it looks like DOB
            if pii_type == 'dob':
                if not self._is_likely_dob(text, full_text, start):
                    return None
            
            return pii_type
        
        return None
    
    def _calculate_confidence(self, ent, text: str) -> float:
        """
        Calculate confidence score for entity using heuristics
        
        Args:
            ent: spaCy entity
            text: Full text for context
        
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.8  # Base confidence for spaCy NER
        
        # Adjust based on entity type and characteristics
        if ent.label_ == 'PERSON':
            # Higher confidence for capitalized multi-word names
            words = ent.text.split()
            if len(words) >= 2 and all(w[0].isupper() for w in words if w):
                confidence += 0.15
            # Lower confidence for single words
            elif len(words) == 1:
                confidence -= 0.2
        
        elif ent.label_ == 'ORG':
            # Organizations with common suffixes get higher confidence
            org_suffixes = ['Inc', 'LLC', 'Ltd', 'Corp', 'Corporation', 'Company', 'Co']
            if any(suffix in ent.text for suffix in org_suffixes):
                confidence += 0.1
        
        # Cap confidence at 1.0
        return min(confidence, 1.0)
    
    def _is_likely_dob(self, date_text: str, full_text: str, start: int) -> bool:
        """
        Check if a date is likely a date of birth based on context
        
        Args:
            date_text: The date text
            full_text: Full text for context
            start: Start position of date
        
        Returns:
            True if likely a DOB
        """
        # Get context BEFORE the date (more important for DOB keywords)
        context_before_start = max(0, start - 50)
        context_before = full_text[context_before_start:start].lower()
        
        # Get small context AFTER the date
        context_after_end = min(len(full_text), start + len(date_text) + 20)
        context_after = full_text[start + len(date_text):context_after_end].lower()
        
        # Check for DOB-related keywords - primarily BEFORE the date
        has_dob_keyword_before = any(keyword in context_before for keyword in self.DOB_CONTEXT_WORDS)
        has_dob_keyword_after = any(keyword in context_after for keyword in self.DOB_CONTEXT_WORDS)
        
        # Keywords should appear before the date (e.g., "born on DATE", "date of birth: DATE")
        # NOT after (which would be a different sentence)
        if not has_dob_keyword_before and not has_dob_keyword_after:
            return False  # Must have DOB keyword
        
        # If keyword only appears after, be very strict
        if has_dob_keyword_after and not has_dob_keyword_before:
            # Only accept if immediately after (within 10 chars)
            immediate_after = full_text[start + len(date_text):start + len(date_text) + 10].lower()
            if not any(keyword in immediate_after for keyword in self.DOB_CONTEXT_WORDS):
                return False
        
        # If keyword found, validate year range for sanity check
        import re
        year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', date_text)
        if year_match:
            year = int(year_match.group(1))
            # Birth years should be in reasonable range (1900-2025)
            return 1900 <= year <= 2025
        
        # Keyword found but no year in text (e.g., "born in March")
        return True
    
    def _is_false_positive(self, text: str, pii_type: str, full_text: str, start: int) -> bool:
        """
        Filter out false positives
        
        Args:
            text: Entity text
            pii_type: Type of PII
            full_text: Full text for context
            start: Start position
        
        Returns:
            True if this is likely a false positive
        """
        # Check blacklist for common words (updated to 'person')
        if pii_type == 'person' and text in self.COMMON_WORD_BLACKLIST:
            return True
        
        # Filter out single-letter "names"
        if pii_type == 'person' and len(text.strip()) <= 1:
            return True
        
        # Filter out all-lowercase "names" (unless it's a known name pattern)
        if pii_type == 'person' and text.islower():
            return True
        
        # Filter out names that are just numbers
        if pii_type == 'person' and text.isdigit():
            return True
        
        # Filter out street names/addresses misclassified as person names
        if pii_type == 'person':
            # Check for address indicators in the text itself
            address_words = ['marg', 'road', 'street', 'avenue', 'lane', 'floor', 'building', 
                           'tower', 'complex', 'plaza', 'center', 'centre', 'reclamation']
            if any(word in text.lower() for word in address_words):
                return True  # This is likely an address, not a person
        
        # Filter regulatory/institutional terms for organizations
        if pii_type == 'organization':
            from ..utils.regulatory_stopwords import is_regulatory_term
            if is_regulatory_term(text):
                return True
        
        # Filter standalone city/country names that aren't part of addresses
        if pii_type == 'location':
            # Common locations that shouldn't be redacted unless part of address
            COMMON_LOCATIONS = {
                'india', 'mumbai', 'delhi', 'bangalore', 'pune', 'hyderabad',
                'chennai', 'kolkata', 'ahmedabad', 'surat',
                'united states', 'usa', 'uk', 'china', 'japan',
                'maharashtra', 'karnataka', 'tamil nadu', 'kerala',
                'gujarat', 'rajasthan', 'delhi', 'goa',
            }
            
            if text.lower() in COMMON_LOCATIONS:
                # Check if part of a full address (has street/building/PIN nearby)
                context_window = 100  # chars
                context_start = max(0, start - context_window)
                context_end = min(len(full_text), start + len(text) + context_window)
                context = full_text[context_start:context_end].lower()
                
                # Address indicators
                address_indicators = [
                    'floor', 'street', 'road', 'building', 'avenue', 'lane',
                    'pin', 'zip', 'postal', r'\d{6}', r'\d{5}',
                    'apartment', 'suite', 'flat', 'tower', 'complex',
                ]
                
                import re
                has_address_context = any(
                    re.search(indicator, context, re.I) 
                    for indicator in address_indicators
                )
                
                if not has_address_context:
                    return True  # Skip standalone locations
        
        return False
    
    def _detect_emails(self, text: str, detected_spans: Set[tuple]) -> List[PIIEntity]:
        """
        Detect email addresses using regex
        
        Args:
            text: Input text
            detected_spans: Set of already detected spans to avoid duplicates
        
        Returns:
            List of email entities
        """
        entities = []
        
        for match in self.patterns['email'].finditer(text):
            span = (match.start(), match.end())
            
            # Skip if already detected by NER
            if any(start <= span[0] < end or start < span[1] <= end 
                   for start, end in detected_spans):
                continue
            
            entity = PIIEntity(
                text=match.group(),
                type='email',
                start=match.start(),
                end=match.end(),
                confidence=0.95  # High confidence for regex email matches
            )
            entities.append(entity)
            detected_spans.add(span)
        
        return entities
    
    def _detect_phones(self, text: str, detected_spans: Set[tuple]) -> List[PIIEntity]:
        """
        Detect phone numbers using regex
        
        Args:
            text: Input text
            detected_spans: Set of already detected spans to avoid duplicates
        
        Returns:
            List of phone entities
        """
        entities = []
        
        for pattern in self.patterns['phone']:
            for match in pattern.finditer(text):
                span = (match.start(), match.end())
                
                # Skip if already detected
                if any(start <= span[0] < end or start < span[1] <= end 
                       for start, end in detected_spans):
                    continue
                
                entity = PIIEntity(
                    text=match.group(),
                    type='phone',
                    start=match.start(),
                    end=match.end(),
                    confidence=0.9  # High confidence for regex phone matches
                )
                entities.append(entity)
                detected_spans.add(span)
        
        return entities
    
    def _remove_overlaps(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """
        Remove overlapping entities, keeping those with higher confidence
        
        Args:
            entities: List of entities
        
        Returns:
            Filtered list without overlaps
        """
        if not entities:
            return entities
        
        # Sort by start position, then by confidence (descending)
        sorted_entities = sorted(entities, key=lambda e: (e.start, -e.confidence))
        
        filtered = []
        last_end = -1
        
        for entity in sorted_entities:
            # Skip if this entity overlaps with the previous one
            if entity.start < last_end:
                # Keep the one with higher confidence
                if filtered and entity.confidence > filtered[-1].confidence:
                    filtered[-1] = entity
                    last_end = entity.end
            else:
                filtered.append(entity)
                last_end = entity.end
        
        return filtered
    
    def generate_replacement(self, entity: PIIEntity) -> str:
        """
        Generate fake replacement for PII entity
        
        Args:
            entity: PIIEntity to replace
        
        Returns:
            Fake replacement value
        """
        original = entity.text
        pii_type = entity.type
        
        # Use FakeDataGenerator for consistent replacements
        if pii_type == 'person':
            return self.fake_generator.generate_name(original)
        
        elif pii_type == 'email':
            return self.fake_generator.generate_email(original)
        
        elif pii_type == 'phone':
            return self.fake_generator.generate_phone(original)
        
        elif pii_type == 'organization':
            return self.fake_generator.generate_company(original)
        
        elif pii_type == 'location':
            # Generate a fake city or location name
            return self.fake_generator.faker.city()
        
        elif pii_type == 'dob':
            return self.fake_generator.generate_dob(original)
        
        else:
            # Fallback: generate generic fake text
            return f"[REDACTED_{pii_type.upper()}]"
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the loaded spaCy model
        
        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.nlp.meta.get('name', 'unknown'),
            'model_version': self.nlp.meta.get('version', 'unknown'),
            'language': self.nlp.meta.get('lang', 'unknown'),
            'pipeline': ', '.join(self.nlp.pipe_names)
        }
    
    def reset(self):
        """Reset the redactor state"""
        super().reset()
        self.fake_generator.clear_cache()
