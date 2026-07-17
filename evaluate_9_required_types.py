"""
Evaluate PII Redaction Tool on Exactly 9 Required PII Types

Required Types (Assignment Scope):
1. Full names (person)
2. Email addresses (email)
3. Phone numbers (phone)
4. Company names (organization)
5. Physical/mailing addresses (address)
6. Social Security Numbers (ssn)
7. Credit card numbers (credit_card)
8. Dates of birth (dob)
9. IP addresses (ip_address)

Additional categories detected but NOT in scope:
- location (merged with address)
- url (out of scope)
- national_id (out of scope)
- medical_license (out of scope, should be 0)
"""
import sys
sys.path.insert(0, '.')
import json
from typing import Dict, List, Set
from src.redactors import RegexRedactor, PresidioRedactor, HybridRedactor
from src.utils.document_handler import DocumentHandler

# Type mapping: internal labels → assignment required labels
TYPE_MAPPING = {
    'person': 'Full names',
    'email': 'Email addresses',
    'phone': 'Phone numbers',
    'organization': 'Company names',
    'address': 'Physical/mailing addresses',
    'location': 'Physical/mailing addresses',  # Merge location → address
    'ssn': 'Social Security Numbers',
    'credit_card': 'Credit card numbers',
    'dob': 'Dates of birth',
    'ip_address': 'IP addresses',
}

# The 9 required types
REQUIRED_TYPES = [
    'Full names',
    'Email addresses',
    'Phone numbers',
    'Company names',
    'Physical/mailing addresses',
    'Social Security Numbers',
    'Credit card numbers',
    'Dates of birth',
    'IP addresses',
]

# Out-of-scope types (report separately)
OUT_OF_SCOPE_TYPES = ['url', 'national_id', 'medical_license', 'driver_license', 'passport']


def normalize_type(detected_type: str) -> str:
    """Map detected type to assignment required type"""
    detected_lower = detected_type.lower().replace('_', ' ').strip()
    
    # Direct mapping
    if detected_lower in TYPE_MAPPING:
        return TYPE_MAPPING[detected_lower]
    
    # Fuzzy matching
    for internal_label, required_label in TYPE_MAPPING.items():
        if internal_label in detected_lower or detected_lower in internal_label:
            return TYPE_MAPPING[internal_label]
    
    # Out of scope
    return None


def load_ground_truth(json_path: str) -> Dict[str, Set[str]]:
    """Load ground truth annotations"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    ground_truth = {}
    for category, items in data.items():
        normalized_cat = normalize_type(category)
        if normalized_cat:  # Only include required types
            if normalized_cat not in ground_truth:
                ground_truth[normalized_cat] = set()
            ground_truth[normalized_cat].update(items)
    
    return ground_truth


def evaluate_redactor(redactor, doc, ground_truth: Dict[str, Set[str]], redactor_name: str):
    """Evaluate a single redactor"""
    print(f"\n{'='*60}")
    print(f"Evaluating: {redactor_name}")
    print(f"{'='*60}")
    
    # Extract text and detect
    text = DocumentHandler.extract_text(doc)
    entities = redactor.detect_pii(text)
    
    # Group detections by required type
    detected = {}
    out_of_scope = {}
    
    for entity in entities:
        entity_type = entity.type
        normalized = normalize_type(entity_type)
        
        if normalized:
            # Required type
            if normalized not in detected:
                detected[normalized] = set()
            detected[normalized].add(entity.text.strip())
        elif entity_type.lower() in OUT_OF_SCOPE_TYPES:
            # Out of scope type
            if entity_type not in out_of_scope:
                out_of_scope[entity_type] = set()
            out_of_scope[entity_type].add(entity.text.strip())
    
    # Calculate metrics for each required type
    results = {}
    
    for req_type in REQUIRED_TYPES:
        gt_set = ground_truth.get(req_type, set())
        det_set = detected.get(req_type, set())
        
        tp = len(gt_set & det_set)  # True positives
        fp = len(det_set - gt_set)  # False positives
        fn = len(gt_set - det_set)  # False negatives
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results[req_type] = {
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'ground_truth_count': len(gt_set),
            'detected_count': len(det_set),
        }
        
        print(f"\n{req_type}:")
        print(f"  Ground Truth: {len(gt_set)}")
        print(f"  Detected: {len(det_set)}")
        print(f"  TP: {tp}, FP: {fp}, FN: {fn}")
        print(f"  Precision: {precision:.2%}")
        print(f"  Recall: {recall:.2%}")
        print(f"  F1: {f1:.2%}")
        
        if fn > 0 and len(gt_set) <= 10:  # Show missed items for small sets
            missed = gt_set - det_set
            print(f"  Missed: {list(missed)[:5]}")
        
        if fp > 0 and len(det_set) <= 20:  # Show false positives
            false_pos = det_set - gt_set
            print(f"  False Positives: {list(false_pos)[:5]}")
    
    # Report out-of-scope detections
    if out_of_scope:
        print(f"\n{'='*60}")
        print("OUT OF SCOPE DETECTIONS (not required by assignment):")
        print(f"{'='*60}")
        for oos_type, oos_items in out_of_scope.items():
            print(f"  {oos_type}: {len(oos_items)} detections")
    
    # Calculate overall metrics
    total_tp = sum(r['tp'] for r in results.values())
    total_fp = sum(r['fp'] for r in results.values())
    total_fn = sum(r['fn'] for r in results.values())
    
    overall_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
    overall_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    print(f"\n{'='*60}")
    print(f"OVERALL METRICS (9 required types only):")
    print(f"{'='*60}")
    print(f"  Precision: {overall_precision:.2%}")
    print(f"  Recall: {overall_recall:.2%}")
    print(f"  F1 Score: {overall_f1:.2%}")
    print(f"  Total TP: {total_tp}, FP: {total_fp}, FN: {total_fn}")
    
    # Check for missing detectors (0 detections across all types)
    zero_detection_types = [t for t in REQUIRED_TYPES if results[t]['detected_count'] == 0 and results[t]['ground_truth_count'] > 0]
    if zero_detection_types:
        print(f"\n⚠️  WARNING: Zero detections for required types:")
        for t in zero_detection_types:
            print(f"    - {t} (ground truth has {results[t]['ground_truth_count']} items)")
            print(f"      → Detector may not exist or not wired up correctly")
    
    return results, overall_precision, overall_recall, overall_f1


def main():
    """Run evaluation on all 4 redactors"""
    print("="*60)
    print("PII REDACTION TOOL - 9 REQUIRED TYPES EVALUATION")
    print("="*60)
    
    # Load test document
    print("\nLoading test document...")
    doc_path = 'tests/test_data/part_1.docx'  # Update with your test file
    ground_truth_path = 'tests/test_data/part_1_ground_truth.json'  # Update with your ground truth
    
    try:
        doc = DocumentHandler.read_document(doc_path)
        ground_truth = load_ground_truth(ground_truth_path)
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease provide:")
        print("  1. Test document: tests/test_data/part_1.docx")
        print("  2. Ground truth: tests/test_data/part_1_ground_truth.json")
        print("\nGround truth JSON format:")
        print("""{
  "Full names": ["John Smith", "Jane Doe"],
  "Email addresses": ["john@example.com"],
  "Phone numbers": ["123-456-7890"],
  "Company names": ["ACME Corp"],
  "Physical/mailing addresses": ["123 Main St, City"],
  "Social Security Numbers": ["123-45-6789"],
  "Credit card numbers": ["4532-1234-5678-9010"],
  "Dates of birth": ["01/15/1980"],
  "IP addresses": ["192.168.1.1"]
}""")
        return
    
    print(f"\n✅ Loaded test document: {doc_path}")
    print(f"✅ Loaded ground truth: {ground_truth_path}")
    print(f"\nGround truth summary:")
    for req_type in REQUIRED_TYPES:
        count = len(ground_truth.get(req_type, set()))
        print(f"  {req_type}: {count}")
    
    # Evaluate all 4 redactors
    redactors = [
        (RegexRedactor(), "Regex Redactor"),
        (PresidioRedactor(), "Presidio Redactor"),
        (HybridRedactor(), "Hybrid Redactor (Recommended)"),
    ]
    
    # Try NER if available
    try:
        from src.redactors import NERRedactor
        redactors.append((NERRedactor(), "NER Redactor (spaCy)"))
    except:
        print("\n⚠️  NER Redactor not available (skipping)")
    
    all_results = {}
    
    for redactor, name in redactors:
        try:
            results, precision, recall, f1 = evaluate_redactor(redactor, doc, ground_truth, name)
            all_results[name] = {
                'results': results,
                'overall': {
                    'precision': precision,
                    'recall': recall,
                    'f1': f1
                }
            }
        except Exception as e:
            print(f"\n❌ Error evaluating {name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate comparison table
    print(f"\n\n{'='*80}")
    print("FINAL COMPARISON TABLE (9 Required PII Types Only)")
    print(f"{'='*80}")
    print(f"\n{'Redactor':<30} {'Precision':<12} {'Recall':<12} {'F1 Score':<12}")
    print("-" * 80)
    
    for name, data in all_results.items():
        overall = data['overall']
        print(f"{name:<30} {overall['precision']:>10.2%}  {overall['recall']:>10.2%}  {overall['f1']:>10.2%}")
    
    # Save results
    output_file = 'evaluation/9_required_types_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n✅ Detailed results saved to: {output_file}")
    print("\nNote: This evaluation covers ONLY the 9 required PII types.")
    print("Additional categories detected (URL, national ID, etc.) are reported")
    print("separately and do NOT affect the precision/recall/F1 metrics above.")


if __name__ == '__main__':
    main()
