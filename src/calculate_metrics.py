"""
Calculate precision, recall, F1 scores for each redactor against ground truth annotations.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from docx import Document

# Import redactors
from src.redactors import RegexRedactor, PresidioRedactor, HybridRedactor


def normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, strip whitespace)."""
    return ' '.join(text.lower().strip().split())


def load_ground_truth(annotation_file: str) -> Dict:
    """Load ground truth annotations from JSON file."""
    with open(annotation_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_text_from_docx(docx_path: str) -> str:
    """Extract full text from DOCX file."""
    doc = Document(docx_path)
    return '\n'.join([para.text for para in doc.paragraphs])


def get_verified_entities(annotations: Dict) -> List[Dict]:
    """Get only verified entities from annotations."""
    verified = []
    for entity in annotations.get('entities', []):
        if entity.get('verified', False):
            verified.append(entity)
    return verified


def normalize_entity_position(text: str, entity: Dict) -> Tuple[int, int]:
    """
    Normalize entity position in text to account for different extraction methods.
    Returns (start_index, end_index) in the full text.
    """
    entity_text = normalize_text(entity['text'])
    normalized_text = normalize_text(text)
    
    # Try to find the entity text in normalized text
    start_idx = normalized_text.find(entity_text)
    if start_idx == -1:
        # Fallback: use original start/end if available
        return (entity.get('start', -1), entity.get('end', -1))
    
    end_idx = start_idx + len(entity_text)
    return (start_idx, end_idx)


def calculate_overlap(range1: Tuple[int, int], range2: Tuple[int, int]) -> float:
    """
    Calculate overlap ratio between two text ranges.
    Returns value between 0.0 (no overlap) and 1.0 (complete overlap).
    """
    start1, end1 = range1
    start2, end2 = range2
    
    if start1 == -1 or start2 == -1:
        return 0.0
    
    # Calculate intersection
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    
    if overlap_start >= overlap_end:
        return 0.0  # No overlap
    
    overlap_len = overlap_end - overlap_start
    
    # Calculate overlap ratio relative to smaller entity
    len1 = end1 - start1
    len2 = end2 - start2
    min_len = min(len1, len2)
    
    if min_len == 0:
        return 0.0
    
    return overlap_len / min_len


def match_detections_to_ground_truth(
    detected_entities: List[Dict],
    ground_truth: List[Dict],
    text: str,
    overlap_threshold: float = 0.5
) -> Tuple[int, int, int]:
    """
    Match detected entities to ground truth entities.
    
    Returns:
        (true_positives, false_positives, false_negatives)
    """
    # Normalize positions for all entities
    gt_positions = []
    for gt_entity in ground_truth:
        pos = normalize_entity_position(text, gt_entity)
        gt_positions.append({
            'position': pos,
            'type': gt_entity['label'],
            'text': gt_entity['text'],
            'matched': False
        })
    
    detected_positions = []
    for det_entity in detected_entities:
        pos = normalize_entity_position(text, det_entity)
        detected_positions.append({
            'position': pos,
            'type': det_entity.get('label', det_entity.get('type', 'unknown')),
            'text': det_entity['text'],
            'matched': False
        })
    
    # Match detected entities to ground truth
    true_positives = 0
    
    for det in detected_positions:
        best_match_idx = -1
        best_overlap = 0.0
        
        for i, gt in enumerate(gt_positions):
            if gt['matched']:
                continue
            
            overlap = calculate_overlap(det['position'], gt['position'])
            
            # Consider it a match if significant overlap (>50%)
            if overlap >= overlap_threshold and overlap > best_overlap:
                best_overlap = overlap
                best_match_idx = i
        
        if best_match_idx >= 0:
            gt_positions[best_match_idx]['matched'] = True
            det['matched'] = True
            true_positives += 1
    
    # Count false positives (detected but not in ground truth)
    false_positives = sum(1 for det in detected_positions if not det['matched'])
    
    # Count false negatives (in ground truth but not detected)
    false_negatives = sum(1 for gt in gt_positions if not gt['matched'])
    
    return true_positives, false_positives, false_negatives


def calculate_metrics(tp: int, fp: int, fn: int) -> Dict[str, float]:
    """Calculate precision, recall, and F1 score."""
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        'precision': round(precision * 100, 2),
        'recall': round(recall * 100, 2),
        'f1': round(f1 * 100, 2),
        'true_positives': tp,
        'false_positives': fp,
        'false_negatives': fn
    }


def evaluate_redactor(redactor, test_file: str, annotation_file: str) -> Dict:
    """Evaluate a single redactor against ground truth."""
    print(f"\n{'='*60}")
    print(f"Evaluating: {redactor.__class__.__name__}")
    print(f"Test File: {os.path.basename(test_file)}")
    print(f"{'='*60}")
    
    # Load ground truth
    annotations = load_ground_truth(annotation_file)
    ground_truth = get_verified_entities(annotations)
    
    print(f"📋 Ground Truth Entities: {len(ground_truth)} (verified only)")
    
    # Extract text
    text = extract_text_from_docx(test_file)
    
    # Run redactor - detect PII in the text
    entities = redactor.detect_pii(text)
    
    # Convert to dict format for matching
    detected = [
        {
            'text': e.text,
            'label': e.type,
            'start': e.start,
            'end': e.end
        }
        for e in entities
    ]
    
    print(f"🔍 Detected Entities: {len(detected)}")
    
    # Match and calculate metrics
    tp, fp, fn = match_detections_to_ground_truth(detected, ground_truth, text)
    metrics = calculate_metrics(tp, fp, fn)
    
    print(f"\n📊 Results:")
    print(f"   True Positives:  {metrics['true_positives']}")
    print(f"   False Positives: {metrics['false_positives']}")
    print(f"   False Negatives: {metrics['false_negatives']}")
    print(f"\n   Precision: {metrics['precision']:.2f}%")
    print(f"   Recall:    {metrics['recall']:.2f}%")
    print(f"   F1 Score:  {metrics['f1']:.2f}%")
    
    return metrics


def main():
    """Main evaluation function."""
    print("\n" + "="*60)
    print("QUANTITATIVE METRICS CALCULATION")
    print("="*60)
    
    # Test files with annotations
    test_cases = [
        {
            'file': 'tests/test_data/part_1.docx',
            'annotation': 'tests/ground_truth/part_1_annotations.json'
        },
        {
            'file': 'tests/test_data/part_2.docx',
            'annotation': 'tests/ground_truth/part_2_annotations.json'
        }
    ]
    
    # Initialize redactors
    redactors = {
        'Regex': RegexRedactor(),
        'Presidio': PresidioRedactor(),
        'Hybrid': HybridRedactor()
    }
    
    # Store all results
    all_results = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0})
    
    # Evaluate each redactor on each test case
    for redactor_name, redactor in redactors.items():
        print(f"\n{'#'*60}")
        print(f"# {redactor_name.upper()} REDACTOR")
        print(f"{'#'*60}")
        
        for test_case in test_cases:
            if not os.path.exists(test_case['file']) or not os.path.exists(test_case['annotation']):
                print(f"⚠️  Skipping {os.path.basename(test_case['file'])} - file not found")
                continue
            
            metrics = evaluate_redactor(redactor, test_case['file'], test_case['annotation'])
            
            # Accumulate results
            all_results[redactor_name]['tp'] += metrics['true_positives']
            all_results[redactor_name]['fp'] += metrics['false_positives']
            all_results[redactor_name]['fn'] += metrics['false_negatives']
    
    # Calculate overall metrics
    print(f"\n{'='*60}")
    print("OVERALL METRICS (ACROSS ALL TEST FILES)")
    print(f"{'='*60}\n")
    
    summary_table = []
    for redactor_name in redactors.keys():
        tp = all_results[redactor_name]['tp']
        fp = all_results[redactor_name]['fp']
        fn = all_results[redactor_name]['fn']
        
        overall = calculate_metrics(tp, fp, fn)
        
        summary_table.append({
            'redactor': redactor_name,
            'precision': overall['precision'],
            'recall': overall['recall'],
            'f1': overall['f1'],
            'tp': tp,
            'fp': fp,
            'fn': fn
        })
        
        print(f"{redactor_name:12} | Precision: {overall['precision']:6.2f}% | Recall: {overall['recall']:6.2f}% | F1: {overall['f1']:6.2f}%")
    
    # Save results to JSON
    output_dir = Path('evaluation')
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / 'quantitative_metrics.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary_table, f, indent=2)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Find best performer
    best_f1 = max(summary_table, key=lambda x: x['f1'])
    print(f"\n🏆 Best Overall Performance: {best_f1['redactor']} (F1: {best_f1['f1']:.2f}%)")
    
    print("\n" + "="*60)
    print("✅ EVALUATION COMPLETE!")
    print("="*60)


if __name__ == '__main__':
    main()
