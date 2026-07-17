# Railway Deployment Guide

## Quick Deploy (GitHub Integration)

### Step 1: Connect to Railway

1. Go to [Railway.app](https://railway.app/)
2. Sign in with GitHub (if not already signed in)
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose repository: `Pri04jain/pii-redaction-tool`
6. Click **"Deploy Now"**

### Step 2: Configure Environment Variables (Optional)

Railway will auto-detect your Python app. If needed, add these variables:

- `PORT` - Auto-set by Railway
- `PYTHON_VERSION` - Set to `3.11.0` (from runtime.txt)

### Step 3: Wait for Build

Railway will:
1. ✅ Detect Python app via `requirements.txt`
2. ✅ Read `nixpacks.toml` for build configuration
3. ✅ Install dependencies
4. ✅ Download spaCy model (`en_core_web_lg`)
5. ✅ Start with gunicorn (from Procfile)

**Build time: ~5-8 minutes** (spaCy model is large)

### Step 4: Get Your URL

Once deployed, Railway provides a URL like:
```
https://pii-redaction-tool-production.up.railway.app
```

Click **"Generate Domain"** to get a public URL.

---

## Alternative: Railway CLI Deployment

If you want to use CLI (optional):

### Install Railway CLI

```bash
# Windows (PowerShell)
iwr https://railway.app/install.ps1 | iex

# Or via npm
npm install -g @railway/cli
```

### Deploy via CLI

```bash
cd "d:\PII Redaction Tool"

# Login to Railway
railway login

# Link to project (if exists) or create new
railway link

# Deploy
railway up

# Open in browser
railway open
```

---

## Verify Deployment

### 1. Health Check

Visit: `https://your-app.railway.app/health`

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### 2. Test Homepage

Visit: `https://your-app.railway.app/`

Should see the PII Redaction Tool interface.

### 3. Test Upload

1. Upload a DOCX file
2. Select "Hybrid" mode (default)
3. Click "Redact PII"
4. Check statistics
5. Download redacted file

---

## Troubleshooting

### Build Fails: "spaCy model not found"

**Fix:** Check `nixpacks.toml` has:
```toml
[phases.install]
cmds = [
    "pip install -r requirements.txt",
    "python -m spacy download en_core_web_lg"
]
```

### Runtime Error: "ModuleNotFoundError"

**Check:**
1. All dependencies in `requirements.txt`
2. Build logs show successful pip install
3. Railway uses Python 3.11 (from `runtime.txt`)

### Timeout Errors

**Fix:** Increase timeout in `Procfile`:
```
web: gunicorn --bind 0.0.0.0:$PORT --timeout 300 --workers 2 src.app:app
```

Already set to 300 seconds (5 minutes).

### Memory Issues

**Symptoms:** App crashes during large file processing

**Fix:** Upgrade Railway plan for more RAM (spaCy + Presidio need ~1-2GB)

---

## Railway Project Settings

Recommended settings:

- **Region**: Choose closest to your location
- **Auto-deploy**: Enable (deploys on every git push to main)
- **Health Check Path**: `/health`
- **Restart Policy**: On failure
- **Environment**: Production

---

## Cost

- **Starter Plan**: $5/month (500 hours)
- **Hobby Plan**: Free tier available (limited hours)

For this project (PII redaction tool):
- Recommended: **Starter Plan** ($5/month)
- Reason: spaCy model needs sufficient RAM

---

## Current Deployment Status

**GitHub Repo**: https://github.com/Pri04jain/pii-redaction-tool

**Latest Commit**: 
```
Fix all PII detection issues + Add 9-type evaluation framework
- Fixed DOB false positives
- Fixed organization over-detection
- Added 9-type evaluation
- Ready for deployment
```

**Files Ready**:
- ✅ `requirements.txt` - All dependencies listed
- ✅ `runtime.txt` - Python 3.11.0
- ✅ `Procfile` - Gunicorn with proper config
- ✅ `nixpacks.toml` - Build instructions for Railway
- ✅ `src/app.py` - Flask app ready

---

## Post-Deployment Testing

### Test Document

Use the test document from `TEST_DATA_GUIDE.md`:

```
CONFIDENTIAL EMPLOYEE RECORD

Employee: John Michael Smith
Email: john.smith@acmecorp.com
Phone: +1-555-234-5678
SSN: 219-09-9999
Credit Card: 4532015112830366
DOB: Born on 01/15/1980
IP: 192.168.1.100
```

### Expected Redactions (Hybrid Mode)

All 9 PII types should be redacted:
- ✅ Full names: "John Michael Smith" → [REDACTED_PERSON]
- ✅ Email: "john.smith@acmecorp.com" → [REDACTED_EMAIL]
- ✅ Phone: "+1-555-234-5678" → [REDACTED_PHONE]
- ✅ SSN: "219-09-9999" → [REDACTED_SSN]
- ✅ Credit Card: "4532015112830366" → [REDACTED_CREDIT_CARD]
- ✅ DOB: "01/15/1980" → [REDACTED_DOB]
- ✅ IP: "192.168.1.100" → [REDACTED_IP_ADDRESS]

### Statistics Check

Expected output:
```json
{
  "person": 1,
  "email": 1,
  "phone": 1,
  "ssn": 1,
  "credit_card": 1,
  "dob": 1,
  "ip_address": 1,
  "total_redactions": 7
}
```

---

## Next Steps After Deployment

1. ✅ Test with sample document
2. ✅ Verify all 9 PII types are detected
3. ✅ Run evaluation with ground truth
4. ✅ Update POC_ANALYSIS.md with live URL
5. ✅ Take screenshots for assignment submission

---

## Support

**Railway Docs**: https://docs.railway.app/
**Railway Discord**: https://discord.gg/railway

For this project:
- Check build logs in Railway dashboard
- Monitor deployment status
- View application logs for errors
