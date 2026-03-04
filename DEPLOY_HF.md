# Deploying to Hugging Face Spaces

## Step 1: Create a Hugging Face Account
1. Go to https://huggingface.co/join
2. Sign up (free)

## Step 2: Create a New Space
1. Go to https://huggingface.co/new-space
2. Fill in:
   - **Space name:** `roar-item-generator`
   - **License:** MIT
   - **SDK:** Gradio
   - **Space hardware:** CPU basic (free) - will auto-upgrade if needed
   - **Visibility:** Public or Private (your choice)
3. Click **"Create Space"**

## Step 3: Clone the Space Repository
```bash
# Install git-lfs if you haven't
brew install git-lfs  # macOS
git lfs install

# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/roar-item-generator
cd roar-item-generator
```

## Step 4: Copy Files to Space
```bash
# From your app directory, copy these files:
cp app_gradio.py roar-item-generator/app.py
cp requirements_hf.txt roar-item-generator/requirements.txt
cp README_HF.md roar-item-generator/README.md
cp difficulty_estimator.py roar-item-generator/
cp -r models roar-item-generator/
cp -r prompts roar-item-generator/
```

## Step 5: Create README.md with metadata
The Space needs a special README with YAML frontmatter. Copy `README_HF.md` content to `README.md` in your space folder.

## Step 6: Add Your API Key as a Secret
1. Go to your Space settings: `https://huggingface.co/spaces/YOUR_USERNAME/roar-item-generator/settings`
2. Click **"New Secret"**
3. Name: `ANTHROPIC_API_KEY`
4. Value: Your Anthropic API key
5. Click **"Save"**

## Step 7: Push to Hugging Face
```bash
cd roar-item-generator
git add .
git commit -m "Initial commit"
git push
```

## Step 8: Wait for Build
- Go to your Space URL: `https://huggingface.co/spaces/YOUR_USERNAME/roar-item-generator`
- Watch the build logs (takes 5-10 min first time)
- Your app will automatically start when ready!

## Benefits:
✅ **16GB RAM** - plenty for ModernBERT
✅ **FREE** - no cost
✅ **Persistent storage** - models cached
✅ **Auto-scaling** - handles traffic spikes
✅ **HTTPS** - secure by default

---

## Alternative: Use the Web Interface (Easier!)

Instead of git commands, you can upload files directly:

1. Create your Space on HuggingFace
2. Click **"Files"** tab
3. Click **"Add file"** → **"Upload files"**
4. Upload:
   - `app_gradio.py` (rename to `app.py`)
   - `requirements_hf.txt` (rename to `requirements.txt`)
   - `difficulty_estimator.py`
   - `README_HF.md` (rename to `README.md`)
   - Entire `models/` folder
   - Entire `prompts/` folder
5. Add your API key in Settings → Secrets
6. Space will auto-build!

This is much easier if you're not comfortable with git.
