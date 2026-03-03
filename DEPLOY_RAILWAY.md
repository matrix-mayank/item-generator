# Deploy to Railway - ROAR Item Generator

## 🚀 Quick Deployment (10 minutes)

### Step 1: Create Railway Account (2 min)
1. Go to https://railway.app
2. Click **"Login"**
3. Sign up with GitHub (easiest)

### Step 2: Create New Project (2 min)
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Click **"Configure GitHub App"**
4. Give Railway access to your `roar-item-generator` repo
5. Select the `roar-item-generator` repository

### Step 3: Configure Environment Variables (2 min)
Railway will start building automatically. While it builds:

1. In your Railway project dashboard, click **"Variables"** tab
2. Click **"New Variable"**
3. Add these variables:
   - **Name:** `ANTHROPIC_API_KEY`
   - **Value:** (paste your API key)
4. Add another:
   - **Name:** `MODEL_PATH`
   - **Value:** `./models`
5. Click **"Deploy"** or it will auto-deploy

### Step 4: Wait for Build (8-10 min)
- Railway will:
  - Install dependencies (PyTorch, transformers, etc.)
  - Build your app
  - Start the server
- Watch the **"Deployments"** tab for progress
- Look for "✅ Build successful"

### Step 5: Get Your URL
1. Click **"Settings"** tab
2. Scroll to **"Networking"**
3. Click **"Generate Domain"**
4. You'll get a URL like: `https://your-app.up.railway.app`

---

## 💰 Pricing
- **$5 free credit** (no credit card needed initially)
- After free credit: **~$5-8/month** (usage-based)
- Starter plan: 8GB RAM, shared CPU
- Enough for ModernBERT + your app

---

## 🔧 What Railway Auto-Detects
✅ Python app (from requirements.txt)
✅ Flask framework
✅ Start command (from Procfile or railway.json)
✅ Port binding (automatically sets $PORT)

---

## 📝 Files Created
- ✅ `Procfile` - tells Railway how to start your app
- ✅ `railway.json` - Railway configuration
- ✅ Already have: requirements.txt, app.py, models/

---

## ⚠️ Important Notes

### Memory Usage
Your app needs ~2-3GB RAM for ModernBERT. Railway starter gives you 8GB, so plenty of space!

### First Deploy
- Takes 10-15 minutes (downloading PyTorch, ModernBERT)
- Subsequent deploys are faster (~5 min)
- First request may be slow while model loads

### Cold Starts
Unlike Render free tier, Railway **doesn't sleep** your app, so no cold starts!

---

## 🐛 Troubleshooting

### Build Fails
1. Check build logs in "Deployments" tab
2. Look for error messages
3. Most common: out of memory → upgrade to more RAM

### App Crashes
1. Check "Logs" tab
2. Look for Python errors
3. Model loading issues → check MODEL_PATH variable

### Can't Access App
1. Make sure domain is generated (Settings → Networking)
2. Check if deployment succeeded (green checkmark)
3. Wait 1-2 minutes after deployment completes

---

## 🎯 After Deployment

Your original Flask app will be live at your Railway URL with:
✅ Your exact custom UI (beige/cream colors, Inter font)
✅ Chat interface on the left
✅ Item preview on the right
✅ Save to collection
✅ Export CSV
✅ Difficulty estimation

No changes to your design! 🎨

---

Need help? Let me know at any step!
