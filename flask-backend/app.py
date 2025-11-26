# flask-backend/app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
from inference_service import InferenceService
import os
from dotenv import load_dotenv
import pymongo
from datetime import datetime

# --- Initialization ---
load_dotenv()
app = Flask(__name__)
CORS(app)

# MongoDB Connection
MONGO_URI = os.getenv("MONGO_URI")
mongo_client = None
reports_collection = None

if MONGO_URI:
    try:
        mongo_client = pymongo.MongoClient(MONGO_URI)
        db = mongo_client.disaster_db
        reports_collection = db.reports
        print("Connected to MongoDB Atlas (disaster_db.reports).")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
else:
    print("WARNING: MONGO_URI not found in environment variables.")

# Load the ML models once when the Flask application starts
try:
    ml_service = InferenceService()
except Exception as e:
    print(f"Failed to initialize InferenceService: {e}")
    ml_service = None

# --- Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """Checks if the service is running and models are loaded."""
    if ml_service and ml_service.disaster_model and ml_service.severity_model:
        return jsonify({"status": "ok", "models_loaded": True}), 200
    return jsonify({"status": "error", "models_loaded": False, "message": "Models failed to load."}), 500


@app.route('/ml/predict', methods=['POST'])
def predict_combined():
    """Runs disaster and severity prediction, extracts location, and saves to MongoDB."""
    if not ml_service or not ml_service.disaster_model:
        return jsonify({"error": "ML Service not ready."}), 503

    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({"error": "Missing 'text' field in request body."}), 400

    try:
        # Get predictions from ML service
        results = ml_service.predict_combined(text)

        # Extract data from results
        disaster_type = results['disaster']['label']
        severity = results['severity']['label']
        location_text = results.get('location')
        coordinates = results.get('coordinates')  # (lat, lon) tuple or None
        
        # Calculate overall confidence
        avg_confidence = (results['disaster']['prob'] + results['severity']['prob']) / 2

        # Prepare location in GeoJSON format (ONLY if coordinates exist)
        location_geojson = None
        if coordinates is not None:
            lat, lon = coordinates
            # CRITICAL: MongoDB GeoJSON requires [longitude, latitude]
            location_geojson = {
                "type": "Point",
                "coordinates": [lon, lat]
            }

        # Construct document for MongoDB
        document = {
            "text": text,
            "disaster_type": disaster_type,
            "severity": severity,
            "location": location_geojson,  # Will be None if no coordinates found
            "location_text": location_text,
            "confidence": round(avg_confidence, 4),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Insert into MongoDB
        if reports_collection is not None:
            try:
                insert_result = reports_collection.insert_one(document)
                # Convert ObjectId to string for JSON serialization
                document['_id'] = str(insert_result.inserted_id)
                print(f"Saved report to MongoDB with ID: {document['_id']}")
            except Exception as e:
                print(f"Error inserting into MongoDB: {e}")
                return jsonify({"error": "Failed to save to database", "details": str(e)}), 500
        else:
            return jsonify({"error": "Database connection not available"}), 503

        return jsonify(document), 200

    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({"error": f"Internal prediction error: {str(e)}"}), 500


if __name__ == '__main__':
    # Running on port 5001
    app.run(debug=True, host='0.0.0.0', port=5001)