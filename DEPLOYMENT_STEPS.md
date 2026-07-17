# Railway Deployment - Step-by-Step Visual Guide

## 🎯 Complete Walkthrough (With Screenshots Reference)

---

## STEP 1: Open Railway and Login

### 1.1 Go to Railway
Open your browser and go to: **https://railway.app/**

### 1.2 Sign In
- Click **"Login"** (top right)
- Choose **"Sign in with GitHub"**
- Authorize Railway to access your GitHub account

**✅ You'll know it worked when:** You see your Railway dashboard

---

## STEP 2: Create New Project from GitHub

### 2.1 Start New Project
- Click the **"New Project"** button (big purple/blue button)
- You'll see several options:
  - Deploy from GitHub repo ← **CHOOSE THIS**
  - Deploy from template
  - Empty project
  - etc.

### 2.2 Select Your Repository
- Click **"Deploy from GitHub repo"**
- Railway will show your GitHub repositories
- Find and click: **`Pri04jain/pii-redaction-tool`**

### 2.3 Confirm Deployment
- Railway shows a preview
- Click **"Deploy Now"** or **"Add variables"** (we don't need variables)

**✅ You'll know it worked when:** Railway starts building (you see logs scrolling)

---

## STEP 3: Watch the Build Process

### 3.1 Build Logs
You'll see a terminal-like window with scrolling text. Look for these lines:

```
✓ Nixpacks build started
✓ Installing Python 3.11
✓ Installing dependencies from requirements.txt
✓ Installing spaCy...
✓ Downloading en_core_web_lg model...  ← THIS TAKES 3-5 MINUTES
✓ Build complete
✓ Starting application...
✓ Server running on port 8080
```

### 3.2 Deployment Status

**Watch the top of the screen for status:**

#### Building (In Progress)
```
🔨 Building...
```
**This means:** Railway is installing dependencies

#### Deploying (Almost Done)
```
🚀 Deploying...
```
**This means:** Build succeeded, starting the app

#### Active (SUCCESS!)
```
✅ Active
```
**This means:** Your app is live and running!

#### Failed (ERROR)
```
❌ Failed
```
**This means:** Something went wrong (we'll fix it)

**✅ You'll know it worked when:** Status shows **"Active"** with a green checkmark

---

## STEP 4: Generate Public URL

### 4.1 Find the Settings
- In your Railway project dashboard
- Look for **"Settings"** tab or **"Networking"** section
- You'll see: **"Domains"** or **"Generate Domain"**

### 4.2 Generate Domain
- Click **"Generate Domain"** button
- Railway automatically creates a URL like:
  ```
  pii-redaction-tool-production.up.railway.app
  ```
  or
  ```
  pii-redaction-tool-production-a1b2.up.railway.app
  ```

### 4.3 Copy Your URL
- The URL appears after generation
- Click the **copy icon** or select and copy it
- Save it somewhere (you'll need it for testing)

**✅ You'll know it worked when:** You have a URL ending in `.railway.app`

---

## STEP 5: Test Your Deployment

### 5.1 Health Check Test

**Open in browser:**
```
https://YOUR-URL.railway.app/health
```

**Replace `YOUR-URL` with your actual Railway URL**

**Expected Result:**
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

**✅ You'll know it worked when:** You see the JSON response above

**❌ If you see an error:**
- "502 Bad Gateway" → App is still starting, wait 30 seconds
- "404 Not Found" → URL might be wrong, check the URL
- "Application Error" → Check Railway logs for errors

---

### 5.2 Homepage Test

**Open in browser:**
```
https://YOUR-URL.railway.app/
```

**Expected Result:**
- You see the **PII Redaction Tool** webpage
- Title: "PII Redaction Tool"
- Upload button
- Mode selector (Regex, NER, Presidio, Hybrid)

**✅ You'll know it worked when:** You see the upload interface

---

### 5.3 Upload Test

**Create a test file:**

1. Open Microsoft Word
2. Type this:
```
EMPLOYEE RECORD

Name: John Michael Smith
Email: john.smith@test.com
Phone: +1-555-234-5678
Company: Acme Corporation
Address: 123 Main Street, New York, NY 10001
SSN: 219-09-9999
Credit Card: 4532015112830366
DOB: Born on 01/15/1980
IP Address: 192.168.1.100
```
3. Save as: `test_employee.docx`

**Upload and Test:**

1. Go to: `https://YOUR-URL.railway.app/`
2. Click **"Choose File"** → Select `test_employee.docx`
3. Select mode: **"Hybrid (Recommended)"**
4. Click **"Redact PII"**

**Wait for processing (10-30 seconds)**

**Expected Result - Statistics Box Shows:**
```
Redaction Statistics:
person: 1
email: 1
phone: 1
organization: 1
address: 1
ssn: 1
credit_card: 1
dob: 1
ip_address: 1

Total Redactions: 9
```

**✅ You'll know it worked when:** 
- You see 9 total redactions
- Download button appears
- Statistics show all 9 PII types

---

## STEP 6: Download and Verify

### 6.1 Download Redacted File
- Click **"Download Redacted Document"** button
- File saves as: `redacted_test_employee.docx`

### 6.2 Open in Word
- Open the downloaded file
- Check that PII is replaced with [REDACTED_XXX]

**Expected Content:**
```
EMPLOYEE RECORD

Name: [REDACTED_PERSON]
Email: [REDACTED_EMAIL]
Phone: [REDACTED_PHONE]
Company: [REDACTED_ORGANIZATION]
Address: [REDACTED_LOCATION]
SSN: [REDACTED_SSN]
Credit Card: [REDACTED_CREDIT_CARD]
DOB: Born on [REDACTED_DATE_TIME]
IP Address: [REDACTED_IP_ADDRESS]
```

**✅ You'll know it worked when:** All sensitive data is replaced with [REDACTED_XXX] tags

---

## 🎯 SUCCESS CHECKLIST

Check off each item as you complete it:

- [ ] **Railway account created** (signed in with GitHub)
- [ ] **Project deployed** (status shows "Active")
- [ ] **Domain generated** (you have a `.railway.app` URL)
- [ ] **Health check works** (`/health` returns JSON)
- [ ] **Homepage loads** (upload interface visible)
- [ ] **Upload works** (can select and upload DOCX file)
- [ ] **Redaction works** (statistics show 9 types detected)
- [ ] **Download works** (redacted file downloaded)
- [ ] **Verification passed** (PII replaced in downloaded file)

**🎉 If all checked: DEPLOYMENT SUCCESSFUL!**

---

## 🐛 Troubleshooting Guide

### Problem 1: Build Fails

**Symptoms:**
- Status shows "Failed" with red X
- Build logs show error messages

**What to check:**

1. **View Build Logs:**
   - Click on the failed deployment
   - Look for error messages in logs

2. **Common Errors:**

   **Error: "requirements.txt not found"**
   ```
   Solution: Check that requirements.txt exists in root
   ```

   **Error: "Failed to download spacy model"**
   ```
   Solution: Check nixpacks.toml has:
   python -m spacy download en_core_web_lg
   ```

   **Error: "Python version not found"**
   ```
   Solution: Check runtime.txt says: python-3.11.0
   ```

3. **How to fix:**
   - Fix the issue in your local code
   - Commit and push to GitHub:
     ```bash
     git add .
     git commit -m "Fix deployment issue"
     git push origin main
     ```
   - Railway auto-redeploys on git push

---

### Problem 2: App Starts But Crashes

**Symptoms:**
- Build succeeds (green checkmark)
- Status changes to "Active" briefly
- Then changes to "Crashed" or "Exited"

**What to check:**

1. **View Application Logs:**
   - Click "View Logs" in Railway dashboard
   - Look for Python errors

2. **Common Errors:**

   **Error: "ModuleNotFoundError: No module named 'spacy'"**
   ```
   Solution: Ensure spacy is in requirements.txt
   Already there? Check that build completed successfully
   ```

   **Error: "OSError: Can't find model 'en_core_web_lg'"**
   ```
   Solution: Build didn't download spacy model
   Check nixpacks.toml has download command
   ```

   **Error: "Address already in use"**
   ```
   Solution: Check Procfile uses $PORT variable:
   gunicorn --bind 0.0.0.0:$PORT src.app:app
   ```

---

### Problem 3: 502 Bad Gateway

**Symptoms:**
- Deployment shows "Active"
- But visiting URL shows "502 Bad Gateway"

**What this means:**
- App is starting but not ready yet
- OR app started but crashed
- OR app is not listening on correct port

**How to fix:**

1. **Wait 30-60 seconds** - App might still be starting

2. **Check logs:**
   - Look for "Server running on port" message
   - Look for crash errors

3. **Verify PORT:**
   - Check Procfile uses `$PORT` variable
   - Railway sets this automatically

---

### Problem 4: Upload Doesn't Work

**Symptoms:**
- Homepage loads fine
- But uploading file shows error

**What to check:**

1. **File Size:**
   - Railway has limits (check your plan)
   - Try smaller test file first

2. **File Type:**
   - Only DOCX files supported
   - Check file extension is .docx

3. **Check Error Message:**
   - Browser console (F12) shows error details
   - Railway logs show server-side errors

---

## 📊 How to Check Railway Logs

### Real-Time Logs

1. **In Railway Dashboard:**
   - Click your project
   - Click **"View Logs"** or **"Deployments"** tab
   - Logs scroll in real-time

2. **What to look for:**

   **Good Signs:**
   ```
   ✓ Starting gunicorn
   ✓ Listening on 0.0.0.0:8080
   ✓ Worker booted with pid: 123
   ```

   **Bad Signs:**
   ```
   ✗ ModuleNotFoundError
   ✗ Failed to bind to 0.0.0.0:8080
   ✗ Worker timeout
   ```

---

## 📸 Take Screenshots for Assignment

Once everything works, take these screenshots:

1. **Railway Dashboard** - Showing "Active" status
2. **Homepage** - Upload interface
3. **Upload Results** - Statistics showing 9 types detected
4. **Redacted Document** - Opened in Word with [REDACTED] tags

---

## 🆘 Still Stuck?

**Share these with me:**

1. **Railway URL** (your `.railway.app` link)
2. **Build logs** (copy last 50 lines)
3. **Application logs** (copy last 50 lines)
4. **Error message** (exact text)

I'll help you debug!

---

## ✅ Final Verification Command

Once deployed, test all 9 PII types:

```bash
# Create test file (on your local machine)
# Upload to Railway URL
# Check stats show:

{
  "person": ✓,
  "email": ✓,
  "phone": ✓,
  "organization": ✓,
  "address": ✓,
  "ssn": ✓,
  "credit_card": ✓,
  "dob": ✓,
  "ip_address": ✓
}
```

**If all 9 types detected → DEPLOYMENT PERFECT! 🎉**
