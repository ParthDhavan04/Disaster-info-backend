# flask-backend/app.py

from flask import Flask, request, jsonify
from inference_service import InferenceService
from flask_cors import CORS

# --- Initialization ---
app = Flask(__name__)
CORS(app)

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
    """Runs both disaster and severity prediction for a single text input."""
    if not ml_service or not ml_service.disaster_model:
        return jsonify({"error": "ML Service not ready."}), 503

    data = request.get_json()
    text = data.get('text')
    input_id = data.get('id', 'N/A')

    if not text:
        return jsonify({"error": "Missing 'text' field in request body."}), 400

    try:
        results = ml_service.predict_combined(text)

        # Calculate overall confidence (e.g., average of two top probabilities)
        avg_prob = (results['disaster']['prob'] + results['severity']['prob']) / 2

        # Placeholder fields set to N/A or None as requested
        response = {
            "id": input_id,
            "disaster": results['disaster'],
            "severity": results['severity'],
            "location_text": "N/A", 
            "lat": None, 
            "lon": None, 
            "confidence": round(avg_prob, 4)
        }
        return jsonify(response)
    
    except Exception as e:
        app.logger.error(f"Prediction error: {e}")
        return jsonify({"error": f"Internal prediction error: {e}"}), 500


@app.route('/ml/predict/disaster', methods=['POST'])
def predict_disaster():
    """Predicts only the disaster type."""
    if not ml_service or not ml_service.disaster_model:
        return jsonify({"error": "ML Service not ready."}), 503

    data = request.get_json()
    text = data.get('text')
    
    if not text:
        return jsonify({"error": "Missing 'text' field."}), 400

    result = ml_service.predict_disaster(text)
    return jsonify(result)


@app.route('/ml/predict/severity', methods=['POST'])
def predict_severity():
    """Predicts only the severity level."""
    if not ml_service or not ml_service.severity_model:
        return jsonify({"error": "ML Service not ready."}), 503

    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({"error": "Missing 'text' field."}), 400

    result = ml_service.predict_severity(text)
    return jsonify(result)


if __name__ == '__main__':
    # Running on port 5001
    app.run(debug=True, host='0.0.0.0', port=5001)