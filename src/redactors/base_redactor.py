"""Base class for all redactor implementations"""
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple
from dataclasses import dataclass
from docx import Document

@dataclass
class PIIEntity:
    """Represents a detected PII entity"""
    text: str
    type: str
    start: int
    end: int
    confidence: float = 1.0

class BaseRedactor(ABC):
    """Abstract base class for PII redactors"""
    
    def __init__(self, consistency_mode: bool = True):
        """
        Initialize redactor
        
        Args:
            consistency_mode: If True, maintain consistent replacements for same values
        """
        self.consistency_mode = consistency_mode
        self.detected_entities: List[PIIEntity] = []
        self.replacements: Dict[str, str] = {}
    
    @abstractmethod
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII in text
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of detected PII entities
        """
        pass
    
    @abstractmethod
    def generate_replacement(self, entity: PIIEntity) -> str:
        """
        Generate fake replacement for PII entity
        
        Args:
            entity: PIIEntity to replace
        
        Returns:
            Fake replacement value
        """
        pass
    
    def redact_text(self, text: str) -> Tuple[str, Dict[str, str]]:
        """
        Redact PII in text
        
        Args:
            text: Input text
        
        Returns:
            Tuple of (redacted_text, replacements_dict)
        """
        entities = self.detect_pii(text)
        
        # Sort by start position (reverse order for replacement)
        entities = sorted(entities, key=lambda x: x.start, reverse=True)
        
        redacted_text = text
        replacements = {}
        
        for entity in entities:
            original = entity.text
            
            # Use cached replacement if consistency mode is on
            if self.consistency_mode and original in self.replacements:
                fake = self.replacements[original]
            else:
                fake = self.generate_replacement(entity)
                self.replacements[original] = fake
            
            replacements[original] = fake
            
            # Replace in text
            redacted_text = redacted_text[:entity.start] + fake + redacted_text[entity.end:]
        
        return redacted_text, replacements
    
    def redact_document(self, doc: Document) -> Tuple[Document, Dict[str, str]]:
        """
        Redact PII in entire document
        
        Args:
            doc: Document object
        
        Returns:
            Tuple of (redacted_document, replacements_dict)
        """
        all_replacements = {}
        
        # Redact paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                entities = self.detect_pii(para.text)
                
                for entity in entities:
                    original = entity.text
                    
                    if self.consistency_mode and original in self.replacements:
                        fake = self.replacements[original]
                    else:
                        fake = self.generate_replacement(entity)
                        self.replacements[original] = fake
                    
                    all_replacements[original] = fake
                    
                    # Replace in paragraph runs
                    for run in para.runs:
                        if original in run.text:
                            run.text = run.text.replace(original, fake)
        
        # Redact tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if para.text.strip():
                            entities = self.detect_pii(para.text)
                            
                            for entity in entities:
                                original = entity.text
                                
                                if self.consistency_mode and original in self.replacements:
                                    fake = self.replacements[original]
                                else:
                                    fake = self.generate_replacement(entity)
                                    self.replacements[original] = fake
                                
                                all_replacements[original] = fake
                                
                                for run in para.runs:
                                    if original in run.text:
                                        run.text = run.text.replace(original, fake)
        
        return doc, all_replacements
    
    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about detected PII"""
        stats = {}
        for entity in self.detected_entities:
            stats[entity.type] = stats.get(entity.type, 0) + 1
        return stats
    
    def reset(self):
        """Reset the redactor state"""
        self.detected_entities.clear()
        self.replacements.clear()
