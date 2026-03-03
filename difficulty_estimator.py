import os
import joblib
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel


class DifficultyEstimator:
    """
    Estimates item difficulty using ModernBERT + PCA + Ridge model.
    Matches the training pipeline from [item_difficulty]_difficulty_estimator_model.py
    """
    
    def __init__(self, model_dir=None):
        self.ridge = None
        self.pca = None
        self.scaler_emb = None
        self.scaler_features = None
        self.grade_columns = None
        self.tokenizer = None
        self.bert_model = None
        self.device = None
        
        if model_dir and os.path.exists(model_dir):
            try:
                print("Loading difficulty model components...")
                
                # Load all artifacts
                self.ridge = joblib.load(f'{model_dir}/ridge_model.pkl')
                self.pca = joblib.load(f'{model_dir}/pca.pkl')
                self.scaler_emb = joblib.load(f'{model_dir}/scaler_emb.pkl')
                self.scaler_features = joblib.load(f'{model_dir}/scaler_features.pkl')
                self.grade_columns = joblib.load(f'{model_dir}/grade_columns.pkl')
                
                print("Loading ModernBERT...")
                self.tokenizer = AutoTokenizer.from_pretrained('answerdotai/ModernBERT-base')
                self.bert_model = AutoModel.from_pretrained('answerdotai/ModernBERT-base')
                self.bert_model.eval()
                self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.bert_model.to(self.device)
                
                print(f"✅ Difficulty model loaded successfully (using {self.device})")
                
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
                import traceback
                traceback.print_exc()
    
    def is_loaded(self):
        """Check if model is fully loaded"""
        return all([
            self.ridge is not None,
            self.pca is not None,
            self.scaler_emb is not None,
            self.scaler_features is not None,
            self.grade_columns is not None,
            self.tokenizer is not None,
            self.bert_model is not None
        ])
    
    def build_text(self, item):
        """
        Build input text matching training format (Figure 2 in paper).
        Format:
        Question: {question}
        Correct: {target_answer}
        Wrong 1: {distractor_1}
        Wrong 2: {distractor_2}
        Wrong 3: {distractor_3}  # Note: your items only have 2 distractors
        Passage: {passage}
        """
        return (
            f"Question: {item.get('question', '')}\n"
            f"Correct: {item.get('target_answer', '')}\n"
            f"Wrong 1: {item.get('distractor_1', '')}\n"
            f"Wrong 2: {item.get('distractor_2', '')}\n"
            f"Wrong 3: \n"  # Empty third distractor since ROAR only has 2
            f"Passage: {item.get('passage', '')}"
        )
    
    def get_embedding(self, text):
        """
        Extract ModernBERT embedding using average pooling over real tokens.
        Matches training code: average over all tokens up to last non-padding.
        """
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=512,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            hidden = outputs.last_hidden_state  # (1, seq_len, hidden_dim)
            mask = inputs['attention_mask']     # (1, seq_len)
            
            # Last non-padding token index
            last_idx = mask[0].nonzero(as_tuple=True)[0][-1].item()
            
            # Average over all real tokens
            real_hidden = hidden[0, :last_idx+1, :]
            avg_emb = real_hidden.mean(dim=0).cpu().numpy()
            
        return avg_emb
    
    def get_grade_ohe(self, grade):
        """
        Create one-hot encoded grade vector.
        ROAR items don't have grade info, so default to Grade4.
        """
        grade_ohe = pd.DataFrame(0, index=[0], columns=self.grade_columns)
        
        # Try to match grade format
        if grade:
            col = f'grade_{grade}'
            if col in self.grade_columns:
                grade_ohe[col] = 1
        else:
            # Default to Grade4 if no grade specified
            if 'grade_Grade4' in self.grade_columns:
                grade_ohe['grade_Grade4'] = 1
        
        return grade_ohe.values
    
    def estimate_difficulty(self, item):
        """
        Estimate difficulty of an item.
        Returns dict with IRT difficulty score or None if model not loaded.
        
        IRT scale interpretation:
        - Negative values = easier items
        - Positive values = harder items
        - Typically ranges from -3 to +3
        """
        if not self.is_loaded():
            return None
        
        try:
            # 1. Build text input
            text = self.build_text(item)
            
            # 2. Get ModernBERT embedding
            emb = self.get_embedding(text)
            
            # 3. Scale -> PCA
            emb_scaled = self.scaler_emb.transform(emb.reshape(1, -1))
            emb_pca = self.pca.transform(emb_scaled)
            
            # 4. Add grade one-hot (default to Grade4 for ROAR items)
            grade = item.get('grade', 'Grade4')
            grade_ohe = self.get_grade_ohe(grade)
            
            # 5. Combine features
            features = np.hstack([emb_pca, grade_ohe])
            
            # 6. Scale and predict
            features_scaled = self.scaler_features.transform(features)
            irt_score = self.ridge.predict(features_scaled)[0]
            
            # Convert IRT score to 0-1 scale for display
            # IRT typically ranges -3 to +3, so we'll map to 0-1
            # where 0 = very easy, 1 = very hard
            normalized_score = (irt_score + 3) / 6
            normalized_score = np.clip(normalized_score, 0, 1)
            
            return {
                'score': float(normalized_score),  # 0-1 for display
                'irt_difficulty': float(irt_score),  # raw IRT score
                'interpretation': self.get_interpretation(normalized_score)
            }
            
        except Exception as e:
            print(f"Error estimating difficulty: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_interpretation(self, score):
        """Get text interpretation of difficulty score"""
        if score < 0.4:
            return "Easy"
        elif score < 0.7:
            return "Medium"
        else:
            return "Hard"
