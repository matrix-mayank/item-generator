"""
Difficulty estimator using BERT-base-cased + PCA + Ridge.
Matches the training pipeline from [item_difficulty]_difficulty_estimator_model (v3).
Expects artifacts in model_dir: ridge_model.pkl, pca.pkl, scaler_emb.pkl, scaler_features.pkl, grade_columns.pkl.
"""

import os
import joblib
import numpy as np
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModel

# Match training script
MAX_LENGTH = 512


class DifficultyEstimator:
    """
    Estimates item difficulty using BERT-base-cased + PCA + Ridge (v3).
    Pipeline: embed text -> scale -> PCA -> concat grade one-hot -> scale -> Ridge -> IRT score.
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

                # Load artifacts saved by the v3 training script
                self.ridge = joblib.load(os.path.join(model_dir, 'ridge_model.pkl'))
                self.pca = joblib.load(os.path.join(model_dir, 'pca.pkl'))
                self.scaler_emb = joblib.load(os.path.join(model_dir, 'scaler_emb.pkl'))
                self.scaler_features = joblib.load(os.path.join(model_dir, 'scaler_features.pkl'))
                self.grade_columns = joblib.load(os.path.join(model_dir, 'grade_columns.pkl'))

                print("Loading BERT (google-bert/bert-base-cased)...")
                self.tokenizer = AutoTokenizer.from_pretrained('google-bert/bert-base-cased')
                self.bert_model = AutoModel.from_pretrained('google-bert/bert-base-cased')
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
        Build input text matching training format (Figure 2 in paper / v3 build_text).
        Training uses: Question, Correct, Wrong 1, Wrong 2, Wrong 3, Passage.
        """
        d1 = item.get('distractor_1', '') or ''
        d2 = item.get('distractor_2', '') or ''
        d3 = item.get('distractor_3', '') or ''
        return (
            f"Question: {item.get('question', '')}\n"
            f"Correct: {item.get('target_answer', '')}\n"
            f"Wrong 1: {d1}\n"
            f"Wrong 2: {d2}\n"
            f"Wrong 3: {d3}\n"
            f"Passage: {item.get('passage', '')}"
        )

    def get_embedding(self, text):
        """
        Extract BERT embedding: average over all real (non-padding) tokens.
        Matches v3 training: last hidden state, average over tokens up to last non-pad.
        """
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=MAX_LENGTH,
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.bert_model(**inputs)
            hidden = outputs.last_hidden_state  # (1, seq_len, hidden_dim)
            mask = inputs['attention_mask']     # (1, seq_len)

            last_idx = mask[0].nonzero(as_tuple=True)[0][-1].item()
            real_hidden = hidden[0, :last_idx + 1, :]
            avg_emb = real_hidden.mean(dim=0).cpu().numpy()

        return avg_emb

    def get_grade_ohe(self, grade):
        """
        One-hot encode grade to match training. Training uses grades like 'Grade3', 'Grade4'.
        grade_columns are e.g. grade_Grade3, grade_Grade4.
        """
        grade_ohe = pd.DataFrame(0, index=[0], columns=self.grade_columns)

        if grade:
            # Accept "Grade4" or 4
            if isinstance(grade, int):
                grade = f'Grade{grade}'
            col = f'grade_{grade}'
            if col in self.grade_columns:
                grade_ohe[col] = 1
        if grade_ohe.values.sum() == 0 and 'grade_Grade4' in self.grade_columns:
            grade_ohe['grade_Grade4'] = 1

        return grade_ohe.values

    def estimate_difficulty(self, item):
        """
        Estimate difficulty of an item. Returns dict with score (0-1), irt_difficulty, interpretation.
        Item may include 'grade' as 'Grade4' or 4 for grade-level; defaults to Grade4.
        """
        if not self.is_loaded():
            return None

        try:
            text = self.build_text(item)
            emb = self.get_embedding(text)

            emb_scaled = self.scaler_emb.transform(emb.reshape(1, -1))
            emb_pca = self.pca.transform(emb_scaled)

            grade = item.get('grade', 'Grade4')
            grade_ohe = self.get_grade_ohe(grade)

            features = np.hstack([emb_pca, grade_ohe])
            features_scaled = self.scaler_features.transform(features)
            irt_score = self.ridge.predict(features_scaled)[0]

            # Map IRT (roughly -3 to +3) to 0-1 for UI
            normalized_score = (irt_score + 3) / 6
            normalized_score = np.clip(normalized_score, 0, 1)

            return {
                'score': float(normalized_score),
                'irt_difficulty': float(irt_score),
                'interpretation': self.get_interpretation(normalized_score)
            }

        except Exception as e:
            print(f"Error estimating difficulty: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_interpretation(self, score):
        """Label for display."""
        if score < 0.4:
            return "Easy"
        elif score < 0.7:
            return "Medium"
        else:
            return "Hard"
