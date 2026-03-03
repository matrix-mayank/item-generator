# ROAR Item Generator - Deployment Guide

## 🚀 Deploy to Render (Recommended - FREE)

### Prerequisites
1. GitHub account
2. Anthropic API key
3. Model files ready in `models/` folder

### Steps:

#### 1. Push to GitHub
```bash
cd "/Users/mayanksharma/Desktop/Item Difficulty/app"

# Initialize git (if not already)
git init

# Add files
git add .

# Commit
git commit -m "Initial commit - ROAR item generator"

# Create repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

#### 2. Deploy on Render

1. Go to https://render.com and sign up/login
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Render will auto-detect `render.yaml` settings
5. Add environment variable:
   - Key: `ANTHROPIC_API_KEY`
   - Value: Your Anthropic API key
6. Click **"Create Web Service"**

#### 3. Wait for Build
- First build takes ~5-10 minutes (installs PyTorch, ModernBERT)
- You'll get a URL like: `https://your-app-name.onrender.com`

### 📝 Important Notes:

**Free Tier Limits:**
- ✅ 512 MB RAM (enough for your model)
- ⚠️ **Sleeps after 15 min inactivity** (30s-1min wake up time)
- ✅ Automatic HTTPS
- ✅ Persistent disk for model files

**First Request After Sleep:**
- Will take 30-60 seconds (cold start + model loading)
- Subsequent requests will be fast

**Model Files:**
- Make sure `models/` folder with all `.pkl` files is committed to git
- Total size should be under 500MB for free tier

### 🔧 Troubleshooting:

If build fails with memory error:
- Upgrade to paid plan ($7/mo for 2GB RAM)
- Or use smaller model/reduce dependencies

If model loading fails:
- Check `MODEL_PATH` environment variable
- Ensure all `.pkl` files are in `models/` folder

### 🎯 Alternative: Keep Paid Tier Awake
If you upgrade to paid ($7/mo):
- No sleep after inactivity
- More RAM (2GB)
- Faster builds

---

## Want to deploy elsewhere?

### Railway (Also free tier available)
1. Install CLI: `npm i -g @railway/cli`
2. `railway login`
3. `railway init`
4. `railway up`

### Hugging Face Spaces (Free, optimized for ML)
1. Create new Space at https://huggingface.co/spaces
2. Choose "Gradio" or "Streamlit"
3. Push your code
4. Models are cached automatically
