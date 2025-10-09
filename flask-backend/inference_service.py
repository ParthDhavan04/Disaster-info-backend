# flask-backend/inference_service.py

import torch
import torch.nn.functional as F
import pickle
import os
from transformers import BertTokenizer, BertForSequenceClassification

# Import the new rule-based validator
from utils.rule_validator import apply_severity_correction

# Define model paths relative to the flask-backend directory (moves up one dir '..')
DISASTER_MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'Fin_Models', 'bert_final_checkpoint')
SEVERITY_MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'Fin_Models', 'bert_severity_checkpoint')


class InferenceService:
    def __init__(self):
        # Determine the device (GPU or CPU)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Loading models to device: {self.device}")
        
        # Load both models at initialization
        self.disaster_tokenizer, self.disaster_model, self.disaster_le = self._load_model_components(
            DISASTER_MODEL_DIR, "Disaster"
        )
        self.severity_tokenizer, self.severity_model, self.severity_le = self._load_model_components(
            SEVERITY_MODEL_DIR, "Severity"
        )

        if self.disaster_model and self.severity_model:
            print("All models loaded successfully.")
        else:
            print("WARNING: Not all models were loaded successfully. Check model paths and file existence.")


    def _load_model_components(self, model_dir, name):
        """Helper function to load tokenizer, model, and LabelEncoder."""
        try:
            tokenizer = BertTokenizer.from_pretrained(model_dir)
            model = BertForSequenceClassification.from_pretrained(model_dir)
            model.to(self.device)
            model.eval()

            le_path = os.path.join(model_dir, "label_encoder.pkl")
            with open(le_path, "rb") as f:
                le = pickle.load(f)
            
            print(f"Loaded {name} model from {model_dir}")
            return tokenizer, model, le
        except Exception as e:
            print(f"ERROR loading {name} model components from {model_dir}: {e}")
            return None, None, None


    def _predict(self, text, tokenizer, model, le):
        """Core prediction function, applying Softmax to get probability."""
        if model is None:
            return {"label": "N/A", "prob": 0.0, "error": "Model not loaded"}

        # Tokenization and input preparation
        inputs = tokenizer(
            text,
            padding='max_length',
            truncation=True,
            max_length=128,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
            # CRITICAL STEP: Apply Softmax to convert logits to probabilities
            probabilities = F.softmax(logits, dim=1)
            
            # Get the predicted class index and the confidence (max probability)
            max_prob, pred_class_id = torch.max(probabilities, dim=1)
            
            # Convert tensors to standard Python types
            predicted_label = le.classes_[pred_class_id.item()]
            confidence = max_prob.item()

        return {"label": predicted_label, "prob": round(confidence, 4)}


    def predict_disaster(self, text):
        return self._predict(text, self.disaster_tokenizer, self.disaster_model, self.disaster_le)

    def predict_severity(self, text):
        return self._predict(text, self.severity_tokenizer, self.severity_model, self.severity_le)

    def predict_combined(self, text):
        # 1. Get ML predictions
        disaster_result = self.predict_disaster(text)
        severity_result = self.predict_severity(text)
        
        # 2. Get the ML predicted severity label
        ml_severity_label = severity_result['label']
        
        # 3. Apply Rule-Based Correction
        corrected_severity_label = apply_severity_correction(text, ml_severity_label)
        
        # 4. If an override occurred, update the severity result label
        if corrected_severity_label != ml_severity_label:
            print(f"Severity OVERRIDE: '{ml_severity_label}' -> '{corrected_severity_label}' for text: '{text[:50]}...'")
            severity_result['label'] = corrected_severity_label
            # NOTE: We keep the original ML probability for confidence measurement.
        
        return {
            "disaster": disaster_result,
            "severity": severity_result
        }