"""POC Evaluation Script - Compare all redactor approaches"""
import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.document_handler import DocumentHandler
from src.redactors import RegexRedactor

# Try to import optional redactors
try:
    from src.redactors import NERRedactor
    NER_AVAILABLE = True
except ImportError:
    NER_AVAILABLE = False
    print("⚠️  NER Redactor not available (spaCy not installed)")

try:
    from src.redactors import PresidioRedactor
    PRESIDIO_AVAILABLE = True
except ImportError:
    PRESIDIO_AVAILABLE = False
    print("⚠️  Presidio Redactor not available")

try:
    from src.redactors import HybridRedactor
    HYBRID_AVAILABLE = True
except ImportError:
    HYBRID_AVAILABLE = False
    print("⚠️  Hybrid Redactor not available")


class POCEvaluator:
    """Evaluate and compare all redactor approaches"""
    
    def __init__(self, test_files: List[str], output_dir: str = "evaluation"):
        """
        Initialize evaluator
        
        Args:
            test_files: List of test document paths
            output_dir: Directory for output files
        """
        self.test_files = test_files
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize available redactors
        self.redactors = {}
        self._init_redactors()
        
        # Results storage
        self.results = {}
    
    def _init_redactors(self):
        """Initialize all available redactors"""
        print("\n" + "="*60)
        print("INITIALIZING REDACTORS")
        print("="*60)
        
        # Regex (always available)
        print("✅ Regex Redactor")
        self.redactors["regex"] = RegexRedactor(consistency_mode=True, seed=42)
        
        # NER (optional)
        if NER_AVAILABLE:
            try:
                print("✅ NER Redactor")
                self.redactors["ner"] = NERRedactor(consistency_mode=True, seed=42)
            except Exception as e:
                print(f"❌ NER Redactor failed: {e}")
        
        # Presidio (optional)
        if PRESIDIO_AVAILABLE:
            try:
                print("✅ Presidio Redactor")
                self.redactors["presidio"] = PresidioRedactor(consistency_mode=True, seed=42)
            except Exception as e:
                print(f"❌ Presidio Redactor failed: {e}")
        
        # Hybrid (optional)
        if HYBRID_AVAILABLE:
            try:
                print("✅ Hybrid Redactor")
                self.redactors["hybrid"] = HybridRedactor(consistency_mode=True, seed=42)
            except Exception as e:
                print(f"❌ Hybrid Redactor failed: {e}")
        
        print(f"\n🎯 Active Redactors: {len(self.redactors)}")
    
    def evaluate_redactor(self, name: str, redactor) -> Dict:
        """
        Evaluate a single redactor
        
        Args:
            name: Redactor name
            redactor: Redactor instance
        
        Returns:
            Dictionary with results
        """
        print(f"\n{'='*60}")
        print(f"TESTING: {name.upper()} REDACTOR")
        print(f"{'='*60}")
        
        total_entities = 0
        total_time = 0
        all_stats = {}
        documents_processed = 0
        
        for test_file in self.test_files:
            if not os.path.exists(test_file):
                print(f"⚠️  File not found: {test_file}")
                continue
            
            print(f"\n📄 Processing: {os.path.basename(test_file)}")
            
            try:
                # Read document
                doc = DocumentHandler.read_document(test_file)
                text = DocumentHandler.extract_text(doc)
                
                # Time the detection
                start_time = time.time()
                entities = redactor.detect_pii(text)
                elapsed_time = time.time() - start_time
                
                total_time += elapsed_time
                total_entities += len(entities)
                documents_processed += 1
                
                # Get statistics
                stats = redactor.get_statistics()
                
                # Merge stats
                for pii_type, count in stats.items():
                    all_stats[pii_type] = all_stats.get(pii_type, 0) + count
                
                print(f"   Detected: {len(entities)} entities in {elapsed_time:.2f}s")
                
                # Generate redacted sample (only for first file to save time)
                if test_file == self.test_files[0]:
                    output_file = self.output_dir / f"redacted_{name}_{os.path.basename(test_file)}"
                    redacted_doc, replacements = redactor.redact_document(doc)
                    DocumentHandler.save_document(redacted_doc, str(output_file))
                    print(f"   💾 Sample saved: {output_file}")
                
                # Reset redactor for next file
                redactor.reset()
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()
        
        # Calculate averages
        avg_time = total_time / documents_processed if documents_processed > 0 else 0
        
        result = {
            "name": name,
            "total_entities": total_entities,
            "total_time": round(total_time, 2),
            "avg_time_per_doc": round(avg_time, 2),
            "documents_processed": documents_processed,
            "stats_by_type": all_stats
        }
        
        print(f"\n📊 Summary:")
        print(f"   Total Entities: {total_entities}")
        print(f"   Total Time: {total_time:.2f}s")
        print(f"   Avg Time/Doc: {avg_time:.2f}s")
        print(f"   PII Types Found: {len(all_stats)}")
        
        return result
    
    def run_evaluation(self):
        """Run evaluation on all redactors"""
        print("\n" + "="*60)
        print("STARTING POC EVALUATION")
        print("="*60)
        print(f"Test Files: {len(self.test_files)}")
        print(f"Redactors: {len(self.redactors)}")
        
        # Evaluate each redactor
        for name, redactor in self.redactors.items():
            try:
                result = self.evaluate_redactor(name, redactor)
                self.results[name] = result
            except Exception as e:
                print(f"\n❌ {name} evaluation failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Generate reports
        self._generate_comparison_report()
        self._save_results_json()
        
        print("\n" + "="*60)
        print("✅ POC EVALUATION COMPLETE!")
        print("="*60)
        print(f"📁 Results saved to: {self.output_dir}")
    
    def _generate_comparison_report(self):
        """Generate markdown comparison report"""
        report = []
        
        report.append("# POC Evaluation Results - Redactor Comparison\n")
        report.append(f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        report.append(f"**Test Files**: {len(self.test_files)}\n")
        report.append(f"**Redactors Tested**: {len(self.results)}\n")
        report.append("\n---\n")
        
        # Overall comparison table
        report.append("## Overall Performance Comparison\n")
        report.append("| Redactor | Total Entities | Avg Time/Doc | PII Types | Status |")
        report.append("|----------|----------------|--------------|-----------|--------|")
        
        for name, result in self.results.items():
            report.append(
                f"| {name.capitalize():<10} | "
                f"{result['total_entities']:>14} | "
                f"{result['avg_time_per_doc']:>11.2f}s | "
                f"{len(result['stats_by_type']):>9} | "
                f"{'✅' if result['documents_processed'] > 0 else '❌'} |"
            )
        
        # Per-category breakdown
        report.append("\n## PII Detection by Category\n")
        
        # Collect all PII types
        all_types = set()
        for result in self.results.values():
            all_types.update(result['stats_by_type'].keys())
        
        if all_types:
            report.append("| PII Type | " + " | ".join([name.capitalize() for name in self.results.keys()]) + " |")
            report.append("|----------|" + "|".join(["------" for _ in self.results]) + "|")
            
            for pii_type in sorted(all_types):
                row = f"| {pii_type} |"
                for result in self.results.values():
                    count = result['stats_by_type'].get(pii_type, 0)
                    row += f" {count} |"
                report.append(row)
        
        # Processing time comparison
        report.append("\n## Processing Time Analysis\n")
        report.append("| Redactor | Total Time | Avg Time/Doc | Speed Rating |")
        report.append("|----------|------------|--------------|--------------|")
        
        for name, result in self.results.items():
            avg_time = result['avg_time_per_doc']
            if avg_time < 1.0:
                speed = "⚡ Fast"
            elif avg_time < 3.0:
                speed = "🐢 Medium"
            else:
                speed = "🐌 Slow"
            
            report.append(
                f"| {name.capitalize():<10} | "
                f"{result['total_time']:>9.2f}s | "
                f"{avg_time:>11.2f}s | "
                f"{speed} |"
            )
        
        # Recommendations
        report.append("\n## Recommendations\n")
        
        if self.results:
            # Find best for entity count
            best_count = max(self.results.items(), key=lambda x: x[1]['total_entities'])
            report.append(f"**Most Comprehensive**: {best_count[0].capitalize()} - Detected {best_count[1]['total_entities']} entities")
            
            # Find fastest
            fastest = min(self.results.items(), key=lambda x: x[1]['avg_time_per_doc'])
            report.append(f"\n**Fastest**: {fastest[0].capitalize()} - {fastest[1]['avg_time_per_doc']:.2f}s per document")
            
            # Overall recommendation
            report.append("\n### Overall Recommendation\n")
            if "hybrid" in self.results:
                report.append("**Recommended: Hybrid Approach**")
                report.append("- Combines strengths of all methods")
                report.append("- Highest detection coverage")
                report.append("- Best balance of accuracy and completeness")
            elif "presidio" in self.results:
                report.append("**Recommended: Presidio**")
                report.append("- Purpose-built for PII detection")
                report.append("- Comprehensive entity coverage")
                report.append("- Good balance of speed and accuracy")
            else:
                report.append("**Recommended: Regex**")
                report.append("- Fast and reliable for structured data")
                report.append("- No external dependencies")
                report.append("- Good for email, phone, SSN detection")
        
        report.append("\n---\n")
        report.append(f"\n*Generated by POC Evaluation Script on {time.strftime('%Y-%m-%d %H:%M:%S')}*\n")
        
        # Save report
        report_path = self.output_dir / "poc_comparison_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))
        
        print(f"\n📊 Comparison report saved: {report_path}")
    
    def _save_results_json(self):
        """Save results as JSON"""
        results_path = self.output_dir / "poc_results.json"
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"💾 Results JSON saved: {results_path}")


def main():
    """Main entry point"""
    print("\n" + "="*60)
    print("PII REDACTION TOOL - POC EVALUATION")
    print("="*60)
    
    # Define test files
    test_files = [
        "tests/test_data/part_1.docx",
        "tests/test_data/part_2.docx",
    ]
    
    # Check if test files exist
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    if not existing_files:
        print("\n❌ No test files found!")
        print("Please ensure test files exist in tests/test_data/")
        return 1
    
    print(f"\n✅ Found {len(existing_files)} test files")
    
    # Create evaluator
    evaluator = POCEvaluator(existing_files)
    
    # Run evaluation
    evaluator.run_evaluation()
    
    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"✅ Redactors tested: {len(evaluator.results)}")
    print(f"📁 Output directory: {evaluator.output_dir}")
    print(f"📊 Report: evaluation/poc_comparison_report.md")
    print(f"💾 Results: evaluation/poc_results.json")
    print(f"📄 Samples: evaluation/redacted_*.docx")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
