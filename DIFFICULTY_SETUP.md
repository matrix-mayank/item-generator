# Setting Up Difficulty Estimation

## Overview
Your difficulty model uses ModernBERT embeddings + PCA + Ridge regression to estimate item difficulty on an IRT scale.

## Steps to Enable Difficulty Estimation

### 1. Download Model Files from Google Drive

From your Google Drive folder `difficulty_model_v3`, download these 5 files:
- `ridge_model.pkl`
- `pca.pkl`
- `scaler_emb.pkl`
- `scaler_features.pkl`
- `grade_columns.pkl`

### 2. Create Model Directory

Create a folder for your model files:
```bash
mkdir -p "/Users/mayanksharma/Desktop/Item Difficulty/app/models"
```

### 3. Place Model Files

Move all 5 downloaded `.pkl` files into:
```
/Users/mayanksharma/Desktop/Item Difficulty/app/models/
```

Your folder structure should look like:
```
app/
├── models/
│   ├── ridge_model.pkl
│   ├── pca.pkl
│   ├── scaler_emb.pkl
│   ├── scaler_features.pkl
│   └── grade_columns.pkl
├── app.py
├── difficulty_estimator.py
├── .env
└── ...
```

### 4. Update .env File

Edit `/Users/mayanksharma/Desktop/Item Difficulty/app/.env` and set:
```
MODEL_PATH=/Users/mayanksharma/Desktop/Item Difficulty/app/models
```

### 5. Install New Dependencies

The model requires PyTorch and Transformers. Install them:
```bash
cd "/Users/mayanksharma/Desktop/Item Difficulty/app"
source venv/bin/activate
pip install torch transformers
```

Or use requirements.txt:
```bash
pip install -r requirements.txt
```

### 6. Restart Flask Server

Stop the current Flask server (Ctrl+C) and restart it:
```bash
python app.py
```

You should see:
```
Loading difficulty model components...
Loading ModernBERT...
✅ Difficulty model loaded successfully (using cpu)
```

## How It Works

Once configured, the app will automatically:

1. **On item generation**: Calculates difficulty for each new item
2. **Display**: Shows difficulty badge in the right sidebar:
   - 🟢 **Green** = Easy (score < 0.4)
   - 🟠 **Orange** = Medium (0.4 - 0.7)
   - 🔴 **Red** = Hard (score > 0.7)
3. **IRT Score**: The raw IRT difficulty (typically -3 to +3) is calculated behind the scenes
4. **CSV Export**: Difficulty scores are included when exporting items

## Model Details

- **Embeddings**: ModernBERT-base (768-dim, reduced via PCA to ~80% variance)
- **Regression**: Ridge regression with optimal lambda
- **Grade**: Defaults to Grade4 for ROAR items (you can add grade field if needed)
- **Performance**: Matches paper's r=0.76, RMSE=0.62 on test set

## Troubleshooting

**If model doesn't load:**
1. Check that all 5 .pkl files are in the models folder
2. Check .env has correct MODEL_PATH
3. Look for error messages in terminal
4. Make sure torch and transformers are installed

**If it's slow:**
- First load takes ~30 seconds (downloads ModernBERT)
- Each prediction takes 1-2 seconds (running BERT inference)
- Consider using GPU for faster inference (set device='cuda')

**If you see "No difficulty estimate":**
- Model may not be loaded (check terminal for error messages)
- Check that the item has all required fields (passage, question, answers)
