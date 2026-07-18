#!/bin/bash
set -e

echo "=================================="
echo "Installing spaCy Model"
echo "=================================="

# Check Python version
python --version

# Check spaCy installation
python -c "import spacy; print(f'spaCy version: {spacy.__version__}')"

# Try to download models in order of preference
for model in en_core_web_sm en_core_web_md en_core_web_lg; do
    echo ""
    echo "Attempting to download: $model"
    if python -m spacy download $model; then
        echo "✅ Successfully downloaded $model"
        
        # Verify it can be loaded
        if python -c "import spacy; nlp = spacy.load('$model'); print(f'✅ Model $model loads successfully')"; then
            echo "✅ Model $model verified and working"
            exit 0
        else
            echo "⚠️ Model $model downloaded but failed to load"
        fi
    else
        echo "❌ Failed to download $model"
    fi
done

echo "❌ All model downloads failed"
exit 1
