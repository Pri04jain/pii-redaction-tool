"""Hybrid PII redactor combining multiple approaches for maximum accuracy"""
from typing import List, Dict, Set
from .base_redactor import BaseRedactor, PIIEntity
from ..utils.fake_data_generator import FakeDataGenerator

# Import all redactors with graceful fallback
from .regex_redactor import RegexRedactor

try:
    from .ner_redactor import NERRedactor
    NER_AVAILABLE = True
except ImportError:
    NER_AVAILABLE = False
    NERRedactor = None

try:
    from .presidio_redactor import PresidioRedactor
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    PresidioRedactor = None


class HybridRedactor(BaseRedactor):
    """
    Hybrid PII redactor combining Regex, NER, and Presidio approaches.
    
    Strategy:
    1. Run regex for structured data (high confidence)
    2. Run NER for contextual entities (if available)
    3. Run Presidio as validator/fallback (if available)
    4. Merge results with deduplication
    5. Resolve conflicts by confidence scores
    
    This provides the best accuracy by leveraging strengths of all approaches.
    """
    
    def __init__(self, consistency_mode: bool = True, seed: int = None,
                 use_ner: bool = True, use_presidio: bool = True,
                 weights: Dict[str, float] = None):
        """
        Initialize hybrid redactor
        
        Args:
            consistency_mode: If True, maintain consistent replacements for same values
            seed: Random seed for reproducible fake data generation
            use_ner: Use NER redactor if available (default: True)
            use_presidio: Use Presidio redactor if available (default: True)
            weights: Confidence weights for each approach
                     Default: {"regex": 1.0, "ner": 1.1, "presidio": 1.2}
        """
        super().__init__(consistency_mode)
        self.fake_generator = FakeDataGenerator(seed)
        
        # Initialize sub-redactors
        self.regex_redactor = RegexRedactor(consistency_mode=False, seed=seed)
        
        self.ner_redactor = None
        if use_ner and NER_AVAILABLE:
            try:
                self.ner_redactor = NERRedactor(consistency_mode=False, seed=seed)
            except Exception as e:
                print(f"Warning: NER redactor initialization failed: {e}")
        
        self.presidio_redactor = None
        if use_presidio and PRESIDIO_AVAILABLE:
            try:
                self.presidio_redactor = PresidioRedactor(consistency_mode=False, seed=seed)
            except Exception as e:
                print(f"Warning: Presidio redactor initialization failed: {e}")
        
        # Confidence weights for each approach (higher = more trustworthy)
        self.weights = weights or {
            "regex": 1.0,      # Baseline
            "ner": 1.1,        # Slightly better for names/orgs
            "presidio": 1.2    # Best overall
        }
    
    def detect_pii(self, text: str) -> List[PIIEntity]:
        """
        Detect PII using all available approaches and merge results
        
        Args:
            text: Input text to analyze
        
        Returns:
            List of detected PII entities with merged confidence scores
        """
        all_entities = []
        
        # 1. Run Regex detection (always available)
        try:
            regex_entities = self.regex_redactor.detect_pii(text)
            # Apply weight to confidence scores
            for entity in regex_entities:
                entity.confidence *= self.weights.get("regex", 1.0)
                all_entities.append(("regex", entity))
        except Exception as e:
            print(f"Warning: Regex detection failed: {e}")
        
        # 2. Run NER detection (if available)
        if self.ner_redactor:
            try:
                ner_entities = self.ner_redactor.detect_pii(text)
                # Apply weight to confidence scores
                for entity in ner_entities:
                    entity.confidence *= self.weights.get("ner", 1.0)
                    all_entities.append(("ner", entity))
            except Exception as e:
                print(f"Warning: NER detection failed: {e}")
        
        # 3. Run Presidio detection (if available)
        if self.presidio_redactor:
            try:
                presidio_entities = self.presidio_redactor.detect_pii(text)
                # Apply weight to confidence scores
                for entity in presidio_entities:
                    entity.confidence *= self.weights.get("presidio", 1.0)
                    all_entities.append(("presidio", entity))
            except Exception as e:
                print(f"Warning: Presidio detection failed: {e}")
        
        # 4. Merge and deduplicate results
        merged_entities = self._merge_entities(all_entities)
        
        # 5. Sort by position
        merged_entities = sorted(merged_entities, key=lambda e: e.start)
        
        # DON'T store here - let base class accumulate
        # self.detected_entities will be populated by base_redactor.redact_document()
        
        return merged_entities
    
    def _merge_entities(self, all_entities: List[tuple]) -> List[PIIEntity]:
        """
        Merge entities from different approaches, handling overlaps and duplicates
        
        Args:
            all_entities: List of (source, entity) tuples
        
        Returns:
            List of merged, deduplicated entities
        """
        if not all_entities:
            return []
        
        # Group entities by overlapping regions
        entity_groups = []
        
        for source, entity in all_entities:
            # Find overlapping group
            added_to_group = False
            
            for group in entity_groups:
                # Check if this entity overlaps with any entity in the group
                for _, existing_entity in group:
                    if self._entities_overlap(entity, existing_entity):
                        group.append((source, entity))
                        added_to_group = True
                        break
                
                if added_to_group:
                    break
            
            # Create new group if no overlap found
            if not added_to_group:
                entity_groups.append([(source, entity)])
        
        # For each group, select the best entity
        merged_entities = []
        
        for group in entity_groups:
            if len(group) == 1:
                # Single detection, use as-is
                _, entity = group[0]
                merged_entities.append(entity)
            else:
                # Multiple overlapping detections, merge them
                best_entity = self._resolve_entity_group(group)
                merged_entities.append(best_entity)
        
        return merged_entities
    
    def _entities_overlap(self, e1: PIIEntity, e2: PIIEntity) -> bool:
        """Check if two entities overlap"""
        return not (e1.end <= e2.start or e2.end <= e1.start)
    
    def _resolve_entity_group(self, group: List[tuple]) -> PIIEntity:
        """
        Resolve a group of overlapping entities by selecting the best one
        
        Strategy:
        1. Prefer entity with highest confidence
        2. If confidence is similar, prefer longer span
        3. If still tied, prefer Presidio > NER > Regex
        
        Args:
            group: List of (source, entity) tuples
        
        Returns:
            Best entity from the group
        """
        # Sort by confidence (descending), then by span length (descending)
        sorted_group = sorted(
            group,
            key=lambda x: (x[1].confidence, x[1].end - x[1].start),
            reverse=True
        )
        
        # Get the best entity
        source, best_entity = sorted_group[0]
        
        # If multiple entities have similar confidence, consider voting
        similar_entities = [
            (s, e) for s, e in sorted_group
            if abs(e.confidence - best_entity.confidence) < 0.1
        ]
        
        if len(similar_entities) > 1:
            # Boost confidence if multiple approaches agree
            best_entity.confidence = min(1.0, best_entity.confidence * 1.1)
        
        return best_entity
    
    def generate_replacement(self, entity: PIIEntity) -> str:
        """
        Generate fake replacement for PII entity
        
        Args:
            entity: PIIEntity to replace
        
        Returns:
            Fake replacement value matching the entity type
        """
        original = entity.text
        entity_type = entity.type
        
        # Normalize type names for consistency
        if entity_type == "name":
            entity_type = "person"  # Unify naming
        if entity_type == "location":
            entity_type = "address"  # Merge location → address
        
        # Use the same generation logic as individual redactors
        if entity_type in ["person"]:
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
        
        elif entity_type in ["address"]:
            return self.fake_generator.generate_address(original)
        
        elif entity_type in ["organization", "company"]:
            return self.fake_generator.generate_company(original)
        
        else:
            # Fallback: use generic placeholder
            return f"[REDACTED_{entity_type.upper()}]"
    
    def get_statistics(self) -> Dict[str, int]:
        """
        Get statistics about detected PII
        
        Returns:
            Dictionary with counts of each PII type
        """
        stats = {}
        for entity in self.detected_entities:
            # Normalize type names for consistency
            normalized_type = entity.type.lower().replace("_", " ")
            stats[normalized_type] = stats.get(normalized_type, 0) + 1
        return stats
    
    def reset(self):
        """Reset the redactor state and all sub-redactors"""
        super().reset()
        self.fake_generator.clear_cache()
        
        # Reset sub-redactors
        if self.regex_redactor:
            self.regex_redactor.reset()
        if self.ner_redactor:
            self.ner_redactor.reset()
        if self.presidio_redactor:
            self.presidio_redactor.reset()
    
    def get_active_redactors(self) -> List[str]:
        """Get list of active redactor approaches"""
        active = ["regex"]
        if self.ner_redactor:
            active.append("ner")
        if self.presidio_redactor:
            active.append("presidio")
        return active
    
    def set_weights(self, weights: Dict[str, float]):
        """
        Update confidence weights for each approach
        
        Args:
            weights: Dictionary mapping approach name to weight value
        """
        self.weights.update(weights)
