"""Regex-based PII redactor implementation"""
import re
from typing import List, Dict, Set
from .base_redactor import BaseRedactor, PIIEntity
from ..utils.pii_patterns import PIIPatterns
from ..utils.fake_data_generator import FakeDataGenerator


class RegexRedactor(BaseRedactor):
    """Fast regex-based PII redactor with high precision for structured data"""
    
    def __init__(self, consistency_mode: bool = True, seed: int = None):
        """
        Initialize regex redactor
        
        Args:
            consistency_mode: If True, maintain consistent replacements for same values
            seed: Random seed for reproducible fake data generation
        """
        super().__init__(consistency_mode)
        self.fake_generator = FakeDataGenerator(seed)
        self.compiled_patterns = PIIPatterns.compile_patterns()
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII in text using regex patterns
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of detected PII entities with confidence scores
        """
        entities = []
        
        # Detect emails (high confidence)
        entities.extend(self._detect_emails(text))
        
        # Detect phone numbers
        entities.extend(self._detect_phones(text))
        
        # Detect SSNs with validation
        entities.extend(self._detect_ssns(text))
        
        # Detect credit cards with Luhn validation
        entities.extend(self._detect_credit_cards(text))
        
        # Detect IP addresses with validation
        entities.extend(self._detect_ip_addresses(text))
        
        # Detect dates of birth
        entities.extend(self._detect_dobs(text))
        
        # Detect addresses
        entities.extend(self._detect_addresses(text))
        
        # Handle overlapping matches - choose longest match
        entities = self._resolve_overlaps(entities)
        
        # Store detected entities
        self.detected_entities = entities
        
        return entities
    
    def _detect_emails(self, text: str) -> List[PIIEntity]:
        """Detect email addresses"""
        entities = []
        pattern = self.compiled_patterns["email"]
        
        for match in pattern.finditer(text):
            entities.append(PIIEntity(
                text=match.group(),
                type="email",
                start=match.start(),
                end=match.end(),
                confidence=0.95  # High confidence for well-formed emails
            ))
        
        return entities
    
    def _detect_phones(self, text: str) -> List[PIIEntity]:
        """Detect phone numbers in multiple formats"""
        entities = []
        
        for pattern in self.compiled_patterns["phone"]:
            for match in pattern.finditer(text):
                phone_text = match.group()
                
                # Basic validation: check if it has enough digits
                digit_count = sum(c.isdigit() for c in phone_text)
                
                # Phone numbers should have at least 10 digits
                if digit_count >= 10:
                    # Higher confidence for international format
                    confidence = 0.9 if phone_text.startswith('+') else 0.8
                    
                    entities.append(PIIEntity(
                        text=phone_text,
                        type="phone",
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence
                    ))
        
        return entities
    
    def _detect_ssns(self, text: str) -> List[PIIEntity]:
        """Detect SSNs with validation"""
        entities = []
        
        for pattern in self.compiled_patterns["ssn"]:
            for match in pattern.finditer(text):
                ssn_text = match.group()
                
                # Validate SSN to reduce false positives
                if PIIPatterns.validate_ssn(ssn_text):
                    # Check context to avoid dates (e.g., "123-45-6789" vs "12-31-2023")
                    # If it has dashes, it's more likely to be SSN format
                    confidence = 0.85 if '-' in ssn_text else 0.7
                    
                    entities.append(PIIEntity(
                        text=ssn_text,
                        type="ssn",
                        start=match.start(),
                        end=match.end(),
                        confidence=confidence
                    ))
        
        return entities
    
    def _detect_credit_cards(self, text: str) -> List[PIIEntity]:
        """Detect credit card numbers with Luhn validation"""
        entities = []
        
        for pattern in self.compiled_patterns["credit_card"]:
            for match in pattern.finditer(text):
                cc_text = match.group()
                
                # Validate using Luhn algorithm
                if PIIPatterns.validate_credit_card(cc_text):
                    entities.append(PIIEntity(
                        text=cc_text,
                        type="credit_card",
                        start=match.start(),
                        end=match.end(),
                        confidence=0.95  # High confidence after Luhn validation
                    ))
        
        return entities
    
    def _detect_ip_addresses(self, text: str) -> List[PIIEntity]:
        """Detect IP addresses with validation"""
        entities = []
        
        # Only process IPv4 for now (first pattern)
        pattern = self.compiled_patterns["ip_address"][0]
        
        for match in pattern.finditer(text):
            ip_text = match.group()
            
            # Validate IP address format
            if PIIPatterns.validate_ip_address(ip_text):
                # Lower confidence for private/common IPs
                confidence = 0.8
                
                # Check if it's a private IP (less sensitive)
                if ip_text.startswith(('192.168.', '10.', '172.')):
                    confidence = 0.6
                
                entities.append(PIIEntity(
                    text=ip_text,
                    type="ip_address",
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence
                ))
        
        return entities
    
    def _detect_dobs(self, text: str) -> List[PIIEntity]:
        """Detect dates of birth"""
        entities = []
        
        for pattern in self.compiled_patterns["dob"]:
            for match in pattern.finditer(text):
                dob_text = match.group()
                
                # Basic validation: check if it looks like a reasonable date
                # This is a simplified check; more sophisticated date validation could be added
                confidence = 0.7  # Medium confidence as dates can be ambiguous
                
                # Higher confidence for spelled-out month format
                if any(month in dob_text.lower() for month in 
                       ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                    confidence = 0.75
                
                entities.append(PIIEntity(
                    text=dob_text,
                    type="dob",
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence
                ))
        
        return entities
    
    def _detect_addresses(self, text: str) -> List[PIIEntity]:
        """Detect physical addresses"""
        entities = []
        
        for pattern in self.compiled_patterns["address"]:
            for match in pattern.finditer(text):
                address_text = match.group()
                
                # Addresses are harder to validate, so lower confidence
                confidence = 0.75
                
                # Higher confidence for PO Box (very specific format)
                if 'P.O. Box' in address_text or 'PO Box' in address_text:
                    confidence = 0.85
                
                entities.append(PIIEntity(
                    text=address_text,
                    type="address",
                    start=match.start(),
                    end=match.end(),
                    confidence=confidence
                ))
        
        return entities
    
    def _resolve_overlaps(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """
        Resolve overlapping matches by choosing the longest match
        
        Args:
            entities: List of detected entities
        
        Returns:
            List of non-overlapping entities
        """
        if not entities:
            return []
        
        # Sort by start position, then by length (longest first)
        entities = sorted(entities, key=lambda e: (e.start, -(e.end - e.start)))
        
        # Track which positions are already covered
        resolved = []
        covered_positions: Set[int] = set()
        
        for entity in entities:
            # Check if this entity overlaps with already selected entities
            entity_positions = set(range(entity.start, entity.end))
            
            if not entity_positions.intersection(covered_positions):
                # No overlap, add to resolved list
                resolved.append(entity)
                covered_positions.update(entity_positions)
        
        # Sort back by position for consistent output
        return sorted(resolved, key=lambda e: e.start)
    
    def generate_replacement(self, entity: PIIEntity) -> str:
        """
        Generate fake replacement for PII entity
        
        Args:
            entity: PIIEntity to replace
        
        Returns:
            Fake replacement value matching the entity type
        """
        original = entity.text
        
        # Generate replacement based on entity type
        if entity.type == "email":
            return self.fake_generator.generate_email(original)
        
        elif entity.type == "phone":
            return self.fake_generator.generate_phone(original)
        
        elif entity.type == "ssn":
            return self.fake_generator.generate_ssn(original)
        
        elif entity.type == "credit_card":
            return self.fake_generator.generate_credit_card(original)
        
        elif entity.type == "ip_address":
            return self.fake_generator.generate_ip_address(original)
        
        elif entity.type == "dob":
            return self.fake_generator.generate_dob(original)
        
        elif entity.type == "address":
            return self.fake_generator.generate_address(original)
        
        else:
            # Fallback: redact with generic placeholder
            return f"[REDACTED_{entity.type.upper()}]"
    
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
