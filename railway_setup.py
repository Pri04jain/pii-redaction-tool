#!/usr/bin/env python
"""Check spaCy installation and download model if missing"""

import sys
import subprocess

def check_and_setup_spacy():
    """Check spaCy installation and download model"""
    
    print("=" * 60)
    print("Railway spaCy Setup Check")
    print("=" * 60)
    
    # Check spaCy installation
    try:
        import spacy
        print(f"✅ spaCy installed: version {spacy.__version__}")
    except ImportError:
        print("❌ spaCy not installed!")
        return False
    
    # Try to load models in order of preference
    models_to_try = ['en_core_web_lg', 'en_core_web_md', 'en_core_web_sm']
    
    for model_name in models_to_try:
        print(f"\nTrying to load: {model_name}")
        try:
            nlp = spacy.load(model_name)
            print(f"✅ Model loaded successfully: {model_name}")
            print(f"   Pipeline: {nlp.pipe_names}")
            return True
        except OSError:
            print(f"❌ Model not found: {model_name}")
            
            # Try to download it
            print(f"   Attempting to download {model_name}...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "spacy", "download", model_name],
                    check=True,
                    capture_output=True,
                    text=True
                )
                print(f"✅ Successfully downloaded {model_name}")
                
                # Try loading again
                nlp = spacy.load(model_name)
                print(f"✅ Model loaded successfully after download")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to download {model_name}")
                print(f"   Error: {e.stderr}")
                continue
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    print("\n❌ No spaCy model could be loaded!")
    print("   This will cause Presidio and NER modes to fail.")
    print("   Only Regex mode will work.")
    return False

if __name__ == "__main__":
    success = check_and_setup_spacy()
    sys.exit(0 if success else 1)
