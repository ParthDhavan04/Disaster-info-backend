# flask-backend/inference_service.py

import torch
import torch.nn.functional as F
import pickle
import os
from transformers import BertTokenizer, BertForSequenceClassification

# Import the new rule-based validator
from utils.rule_validator import apply_severity_correction
import spacy
from geopy.geocoders import Nominatim

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

        # Initialize Spacy and Geopy
        try:
            # UPGRADED to medium model for better NER accuracy
            self.nlp = spacy.load("en_core_web_md")
            print("Spacy model 'en_core_web_md' loaded.")
        except Exception as e:
            print(f"Error loading spacy model: {e}")
            print("Trying fallback to 'en_core_web_sm'...")
            try:
                self.nlp = spacy.load("en_core_web_sm")
                print("Spacy model 'en_core_web_sm' loaded.")
            except Exception as e2:
                print(f"Error loading fallback spacy model: {e2}")
                self.nlp = None

        self.geolocator = Nominatim(user_agent="disaster_app_v1")


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

    def extract_location(self, text):
        """
        Extracts the first entity that is a valid location and returns (text, coordinates).
        Checks GPE, LOC, FAC, and ORG (common misclassification) labels.
        Verifies validity by attempting to geocode.
        Filters out generic/blocklisted terms.
        """
        print(f"Analyzing text for location: {text}")
        
        if not self.nlp:
            return None, None
        
        # Blocklist of generic terms to skip
        blocklist = ["india", "time", "date", "bbc", "news", "reuters", "update", "situation report"]
        
        doc = self.nlp(text)
        valid_labels = ['GPE', 'LOC', 'FAC', 'ORG']
        
        for ent in doc.ents:
            if ent.label_ in valid_labels:
                print(f" - Found Entity: '{ent.text}' ({ent.label_})")
                
                # Skip very short entities to avoid false positives
                if len(ent.text) < 2:
                    continue
                
                # Check blocklist (case-insensitive)
                if ent.text.lower() in blocklist:
                    print(f" -> Blocklisted: {ent.text}")
                    continue
                    
                # Verify if it's a real location using the geolocator
                # Returns (lat, lon) if valid
                coords = self.get_coordinates(ent.text)
                print(f" -> Geocoded '{ent.text}': {coords}")
                
                if coords:
                    return ent.text, coords  # Return BOTH name and coords
        
        return None, None

    def get_coordinates(self, location_name):
        """Fetches coordinates for a given location name, restricted to India."""
        if not location_name:
            return None
        try:
            # timeout added to prevent hanging, country_codes restricts to India
            location = self.geolocator.geocode(location_name, country_codes="in", timeout=5)
            
            # Fallback: Try without country code if first attempt fails (sometimes helps with specific landmarks)
            if not location:
                 location = self.geolocator.geocode(location_name, timeout=5)
            
            if location:
                return (location.latitude, location.longitude)
        except Exception as e:
            print(f"Geocoding error for '{location_name}': {e}")
        return None

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
            print(f"Severity OVERRIDE: '{ml_severity_label}' -> '{corrected_severity_label}'")
            severity_result['label'] = corrected_severity_label
            # NOTE: We keep the original ML probability for confidence measurement.
        
        # 5. Extract Location and Coordinates (OPTIMIZED: One call only)
        location_text, coordinates = self.extract_location(text)

        return {
            "disaster": disaster_result,
            "severity": severity_result,
            "location": location_text,
            "coordinates": coordinates
        }