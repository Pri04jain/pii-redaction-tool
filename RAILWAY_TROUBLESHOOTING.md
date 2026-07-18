# Railway Deployment Troubleshooting

## How to Check Logs on Railway

1. Go to your Railway project dashboard
2. Click on your deployment
3. Click on **"Deployments"** tab
4. Click on the latest deployment
5. Click **"View Logs"** button

## Common Errors and Solutions

### Error: "Redaction Failed"

This is a generic error. Check the Railway logs for the actual error message.

#### Solution 1: Missing spaCy Model

**Symptom in logs:**
```
OSError: [E050] Can't find model 'en_core_web_lg'
```

**Fix:**
The `nixpacks.toml` file should handle this automatically. If it doesn't:

1. Check Railway build logs - look for:
   ```
   ✅ Successfully installed en-core-web-lg-3.7.1
   ```

2. If not found, add environment variable in Railway:
   - Key: `SPACY_MODEL`
   - Value: `en_core_web_sm` (smaller fallback model)

#### Solution 2: Memory Issues

**Symptom in logs:**
```
Killed
```
or
```
MemoryError
```

**Fix:**
1. Upgrade Railway plan (Starter plan recommended)
2. Or reduce workers in Procfile:
   ```
   web: gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 1 src.app:app
   ```

#### Solution 3: Import Errors

**Symptom in logs:**
```
ModuleNotFoundError: No module named 'presidio_analyzer'
```

**Fix:**
Check `requirements.txt` has all dependencies:
```
presidio-analyzer==2.2.354
presidio-anonymizer==2.2.354
spacy==3.7.4
```

#### Solution 4: Presidio Initialization Failed

**Symptom in logs:**
```
RuntimeError: Failed to initialize Presidio engines
```

**Fix:**
This usually means spaCy model is missing. The app will fallback to regex mode.

Test with:
```bash
curl https://your-app.railway.app/health
```

Check the response for `spacy_model_loaded: true`

### Error: "502 Bad Gateway"

**Symptom:** App crashes immediately or doesn't start

**Possible causes:**
1. Port binding issue
2. Import error during startup
3. Missing dependencies

**Fix:**
1. Check Railway logs for startup errors
2. Verify `PORT` environment variable is set (Railway sets this automatically)
3. Test health endpoint: `https://your-app.railway.app/health`

### Error: "413 Request Entity Too Large"

**Symptom:** Large files fail to upload

**Fix:**
Add environment variable in Railway:
- Key: `MAX_FILE_SIZE`
- Value: `104857600` (100MB in bytes)

## Debugging Steps

### Step 1: Check Health Endpoint

Visit: `https://your-app.railway.app/health`

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {
    "spacy_available": true,
    "spacy_model_loaded": true,
    "spacy_model": "en_core_web_lg",
    "presidio_available": true,
    "ner_available": true
  }
}
```

If any dependency is `false`, that's your issue.

### Step 2: Test with Simple File

Create a test DOCX with:
```
John Smith
john@example.com
555-123-4567
```

Upload and check Railway logs for detailed error messages.

### Step 3: Check Build Logs

In Railway dashboard:
1. Go to Deployments
2. Click on latest deployment
3. Look for these successful steps:
   - ✅ `pip install -r requirements.txt`
   - ✅ `python -m spacy download en_core_web_lg`
   - ✅ Build completed successfully

### Step 4: Check Runtime Logs

Look for these in logs:
```
🚀 PII Redaction Tool Server Starting...
INFO - Upload folder: /app/uploads
INFO - Output folder: /app/output
INFO - NER Available: True
```

## Railway CLI Commands

If you have Railway CLI installed:

```bash
# View live logs
railway logs

# Check environment variables
railway variables

# SSH into container
railway shell

# Test spaCy model
railway run python -c "import spacy; nlp = spacy.load('en_core_web_lg'); print('OK')"
```

## Manual Test Script

Create `test_railway.py` locally:

```python
import requests

BASE_URL = "https://your-app.railway.app"

# Test health
response = requests.get(f"{BASE_URL}/health")
print("Health check:", response.json())

# Test upload
files = {'file': open('test.docx', 'rb')}
data = {'mode': 'regex'}  # Start with regex (simplest)
response = requests.post(f"{BASE_URL}/upload", files=files, data=data)
print("Upload response:", response.json())
```

Run:
```bash
python test_railway.py
```

## Environment Variables to Set

In Railway dashboard, add these if needed:

| Variable | Value | Purpose |
|----------|-------|---------|
| `PORT` | (auto-set) | Port to bind to |
| `FLASK_ENV` | `production` | Run in production mode |
| `MAX_FILE_SIZE` | `52428800` | 50MB file limit |
| `SPACY_MODEL` | `en_core_web_lg` | spaCy model to use |
| `SECRET_KEY` | (random string) | Flask secret key |

## Quick Fixes

### Fallback to Smaller Model

If `en_core_web_lg` fails, update `nixpacks.toml`:

```toml
[phases.install]
cmds = [
    "pip install --upgrade pip",
    "pip install -r requirements.txt",
    "python -m spacy download en_core_web_sm"
]
```

Then redeploy.

### Reduce Memory Usage

Update `Procfile`:
```
web: gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 1 --max-requests 100 src.app:app
```

### Test Locally with Railway Environment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Run locally with Railway environment
railway run python src/app.py
```

## Getting More Help

1. **Check Railway logs** - Most errors show up here
2. **Test health endpoint** - Shows which dependencies are loaded
3. **Try regex mode first** - Simplest, no heavy dependencies
4. **Check this repo's issues** - Similar problems may be solved

## Contact

If you're still stuck:
1. Copy the exact error from Railway logs
2. Include response from `/health` endpoint
3. Note which redaction mode you're using
4. Open an issue on GitHub
