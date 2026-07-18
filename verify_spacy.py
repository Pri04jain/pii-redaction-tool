#!/usr/bin/env python
"""Verify spaCy model installation"""
import sys

try:
    import spacy
    print(f"✅ spaCy version: {spacy.__version__}")
    
    # Check for installed models
    models = list(spacy.util.get_installed_models())
    print(f"📦 Installed models: {models}")
    
    if not models:
        print("❌ No spaCy models installed!")
        sys.exit(1)
    
    # Try to load a model
    model_name = models[0] if models else 'en_core_web_sm'
    print(f"🔄 Loading model: {model_name}")
    nlp = spacy.load(model_name)
    print(f"✅ Successfully loaded: {nlp.meta['name']} v{nlp.meta['version']}")
    print(f"📋 Pipeline components: {nlp.pipe_names}")
    
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
