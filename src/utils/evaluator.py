"""Evaluation utilities for measuring redaction performance"""
from typing import Dict, List, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class Annotation:
    """Ground truth annotation"""
    text: str
    type: str
    start: int
    end: int
    document: str = ""
    paragraph: int = 0

@dataclass
class EvaluationMetrics:
    """Evaluation metrics container"""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    true_negatives: int = 0
    
    @property
    def precision(self) -> float:
        """Calculate precision"""
        if self.true_positives + self.false_positives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_positives)
    
    @property
    def recall(self) -> float:
        """Calculate recall"""
        if self.true_positives + self.false_negatives == 0:
            return 0.0
        return self.true_positives / (self.true_positives + self.false_negatives)
    
    @property
    def f1_score(self) -> float:
        """Calculate F1 score"""
        if self.precision + self.recall == 0:
            return 0.0
        return 2 * (self.precision * self.recall) / (self.precision + self.recall)
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy"""
        total = self.true_positives + self.true_negatives + self.false_positives + self.false_negatives
        if total == 0:
            return 0.0
        return (self.true_positives + self.true_negatives) / total
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "true_negatives": self.true_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "accuracy": round(self.accuracy, 4)
        }

class Evaluator:
    """Evaluate redaction performance against ground truth"""
    
    @staticmethod
    def load_ground_truth(file_path: str) -> List[Annotation]:
        """Load ground truth annotations from JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        annotations = []
        for item in data:
            annotations.append(Annotation(
                text=item['text'],
                type=item['type'],
                start=item['start'],
                end=item['end'],
                document=item.get('document', ''),
                paragraph=item.get('paragraph', 0)
            ))
        
        return annotations
    
    @staticmethod
    def save_ground_truth(annotations: List[Annotation], file_path: str):
        """Save ground truth annotations to JSON file"""
        data = [
            {
                "text": ann.text,
                "type": ann.type,
                "start": ann.start,
                "end": ann.end,
                "document": ann.document,
                "paragraph": ann.paragraph
            }
            for ann in annotations
        ]
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def calculate_overlap(start1: int, end1: int, start2: int, end2: int) -> float:
        """Calculate overlap ratio between two spans"""
        overlap_start = max(start1, start2)
        overlap_end = min(end1, end2)
        
        if overlap_start >= overlap_end:
            return 0.0
        
        overlap_length = overlap_end - overlap_start
        span1_length = end1 - start1
        
        return overlap_length / span1_length
    
    @staticmethod
    def evaluate(detected: List[Annotation], ground_truth: List[Annotation], 
                overlap_threshold: float = 0.5) -> EvaluationMetrics:
        """
        Evaluate detected entities against ground truth
        
        Args:
            detected: List of detected entities
            ground_truth: List of ground truth annotations
            overlap_threshold: Minimum overlap ratio to consider a match
        
        Returns:
            EvaluationMetrics object
        """
        metrics = EvaluationMetrics()
        
        matched_gt = set()
        matched_detected = set()
        
        # Find true positives
        for i, det in enumerate(detected):
            for j, gt in enumerate(ground_truth):
                if j in matched_gt:
                    continue
                
                # Check if same type
                if det.type != gt.type:
                    continue
                
                # Check overlap
                overlap = Evaluator.calculate_overlap(det.start, det.end, gt.start, gt.end)
                
                if overlap >= overlap_threshold:
                    metrics.true_positives += 1
                    matched_gt.add(j)
                    matched_detected.add(i)
                    break
        
        # False positives: detected but not in ground truth
        metrics.false_positives = len(detected) - len(matched_detected)
        
        # False negatives: in ground truth but not detected
        metrics.false_negatives = len(ground_truth) - len(matched_gt)
        
        # Note: True negatives are hard to calculate for text (infinite non-PII spans)
        # We set it to 0 for this use case
        metrics.true_negatives = 0
        
        return metrics
    
    @staticmethod
    def evaluate_by_category(detected: List[Annotation], ground_truth: List[Annotation]) -> Dict[str, EvaluationMetrics]:
        """Evaluate performance for each PII category"""
        categories = set([ann.type for ann in ground_truth + detected])
        
        results = {}
        for category in categories:
            cat_detected = [ann for ann in detected if ann.type == category]
            cat_ground_truth = [ann for ann in ground_truth if ann.type == category]
            
            results[category] = Evaluator.evaluate(cat_detected, cat_ground_truth)
        
        return results
    
    @staticmethod
    def generate_report(metrics: EvaluationMetrics, category_metrics: Dict[str, EvaluationMetrics] = None) -> str:
        """Generate evaluation report"""
        report = []
        report.append("=" * 60)
        report.append("PII REDACTION EVALUATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        report.append("Overall Metrics:")
        report.append("-" * 60)
        report.append(f"Precision:  {metrics.precision:.2%}")
        report.append(f"Recall:     {metrics.recall:.2%}")
        report.append(f"F1 Score:   {metrics.f1_score:.2%}")
        report.append(f"Accuracy:   {metrics.accuracy:.2%}")
        report.append("")
        report.append(f"True Positives:  {metrics.true_positives}")
        report.append(f"False Positives: {metrics.false_positives}")
        report.append(f"False Negatives: {metrics.false_negatives}")
        report.append("")
        
        if category_metrics:
            report.append("Per-Category Metrics:")
            report.append("-" * 60)
            report.append(f"{'Category':<20} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
            report.append("-" * 60)
            
            for category, cat_metrics in sorted(category_metrics.items()):
                report.append(
                    f"{category:<20} "
                    f"{cat_metrics.precision:<12.2%} "
                    f"{cat_metrics.recall:<12.2%} "
                    f"{cat_metrics.f1_score:<12.2%}"
                )
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)
    
    @staticmethod
    def create_annotation_template(text: str, output_path: str):
        """Create annotation template for manual labeling"""
        template = {
            "text": text[:500] + "..." if len(text) > 500 else text,
            "instructions": "Add annotations in the format below",
            "annotations": [
                {
                    "text": "example@email.com",
                    "type": "EMAIL",
                    "start": 0,
                    "end": 17,
                    "document": "example.docx",
                    "paragraph": 0
                }
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
