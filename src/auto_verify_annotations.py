"""Automatically verify obvious true/false positives in annotations"""
import json
import re
from datetime import datetime
from pathlib import Path


def auto_verify_annotation(annotation: dict, context_text: str = "") -> tuple:
    """
    Automatically verify if an annotation is likely correct
    
    Returns:
        (verified: bool, confidence: str, reason: str)
    """
    text = annotation["text"]
    pii_type = annotation["type"]
    
    # Email - usually correct
    if pii_type == "email":
        if "@" in text and "." in text:
            return (True, "high", "Valid email format")
        return (False, "high", "Invalid email format")
    
    # Phone - check format
    if pii_type == "phone":
        digits = re.sub(r'\D', '', text)
        if len(digits) >= 10:
            return (True, "high", "Valid phone format")
        return (False, "high", "Too few digits for phone")
    
    # DOB - check if it's a reasonable birth date
    if pii_type == "dob":
        # Extract year
        year_match = re.search(r'\b(19\d{2}|20[0-2]\d)\b', text)
        if year_match:
            year = int(year_match.group(1))
            current_year = datetime.now().year
            
            # Future dates are NOT birth dates
            if year > current_year:
                return (False, "high", f"Future date ({year}) - not a DOB")
            
            # Very recent dates unlikely to be DOB in business doc
            if current_year - year < 18:
                return (False, "medium", f"Too recent ({year}) - likely document date")
            
            # Reasonable birth year range (18-100 years old)
            if 1920 <= year <= 2006:
                # Check context for DOB keywords
                if any(keyword in context_text.lower() for keyword in ['birth', 'born', 'dob', 'age']):
                    return (True, "high", f"Valid birth year ({year}) with DOB context")
                return (None, "low", f"Valid birth year ({year}) but no DOB context - needs review")
            
            # Very old dates
            if year < 1920:
                return (False, "medium", f"Too old ({year}) - unlikely to be DOB")
        
        return (None, "low", "Date format but uncertain - needs review")
    
    # Address - check for street indicators
    if pii_type == "address":
        street_indicators = ['street', 'st', 'avenue', 'ave', 'road', 'rd', 'drive', 'dr', 'lane', 'ln', 'boulevard', 'blvd']
        text_lower = text.lower()
        
        # Contains street indicator
        if any(ind in text_lower for ind in street_indicators):
            # Check if it starts with a number (typical address format)
            if re.match(r'^\d+', text):
                return (True, "high", "Contains street indicator and starts with number")
            return (True, "medium", "Contains street indicator")
        
        # PO Box
        if 'p.o. box' in text_lower or 'po box' in text_lower:
            return (True, "high", "PO Box address")
        
        # May be just a number or partial text
        if len(text) < 10:
            return (False, "medium", "Too short to be complete address")
        
        return (None, "low", "Uncertain address pattern - needs review")
    
    # SSN - validate format
    if pii_type == "ssn":
        digits = re.sub(r'\D', '', text)
        if len(digits) == 9:
            return (True, "high", "Valid SSN format (9 digits)")
        return (False, "high", "Invalid SSN format")
    
    # Credit Card - validate length
    if pii_type == "credit_card":
        digits = re.sub(r'\D', '', text)
        if 15 <= len(digits) <= 16:
            return (True, "medium", "Valid credit card length")
        return (False, "high", "Invalid credit card length")
    
    # IP Address - validate format
    if pii_type == "ip_address":
        parts = text.split('.')
        if len(parts) == 4:
            try:
                if all(0 <= int(p) <= 255 for p in parts):
                    return (True, "high", "Valid IPv4 format")
            except:
                pass
        return (False, "high", "Invalid IP format")
    
    # Default - needs review
    return (None, "low", "Needs manual review")


def process_annotation_file(input_path: str, output_path: str):
    """Process annotation file and auto-verify where possible"""
    print(f"\n{'='*60}")
    print(f"Processing: {input_path}")
    print(f"{'='*60}")
    
    # Load annotations
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    annotations = data['annotations']
    total = len(annotations)
    
    auto_verified_true = 0
    auto_verified_false = 0
    needs_review = 0
    
    for ann in annotations:
        verified, confidence, reason = auto_verify_annotation(ann)
        
        ann['auto_verified'] = verified
        ann['auto_confidence'] = confidence
        ann['auto_reason'] = reason
        
        if verified is True:
            ann['verified'] = True
            auto_verified_true += 1
        elif verified is False:
            ann['verified'] = False
            auto_verified_false += 1
        else:
            needs_review += 1
            ann['notes'] = f"⚠️ NEEDS REVIEW: {reason}"
    
    # Save updated annotations
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"   Total annotations: {total}")
    print(f"   ✅ Auto-verified TRUE: {auto_verified_true} ({auto_verified_true/total*100:.1f}%)")
    print(f"   ❌ Auto-verified FALSE: {auto_verified_false} ({auto_verified_false/total*100:.1f}%)")
    print(f"   ⚠️  Needs manual review: {needs_review} ({needs_review/total*100:.1f}%)")
    
    # Show what needs review
    if needs_review > 0:
        print(f"\n⚠️  Items needing review:")
        review_items = [ann for ann in annotations if ann['auto_verified'] is None]
        for i, ann in enumerate(review_items[:10], 1):
            print(f"   {i}. [{ann['type']}] '{ann['text'][:40]}...' - {ann['auto_reason']}")
        if len(review_items) > 10:
            print(f"   ... and {len(review_items) - 10} more")
    
    print(f"\n✅ Saved to: {output_path}")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("AUTO-VERIFY ANNOTATIONS")
    print("="*60)
    print("\nThis script automatically verifies obvious cases:")
    print("  ✅ TRUE: Clear PII (valid format, reasonable values)")
    print("  ❌ FALSE: Clear false positives (future dates, invalid formats)")
    print("  ⚠️  REVIEW: Ambiguous cases needing human verification")
    
    files = [
        "tests/ground_truth/part_1_annotations.json",
        "tests/ground_truth/part_2_annotations.json",
    ]
    
    for file_path in files:
        try:
            process_annotation_file(file_path, file_path)
        except Exception as e:
            print(f"\n❌ Error processing {file_path}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("✅ AUTO-VERIFICATION COMPLETE")
    print("="*60)
    print("\n📝 Next steps:")
    print("   1. Open the JSON files")
    print("   2. Review items marked '⚠️ NEEDS REVIEW'")
    print("   3. Manually verify those annotations")
    print("   4. Add any MISSED PII as new entries")
    print("   5. Run evaluation to get precision/recall metrics")


if __name__ == "__main__":
    main()
