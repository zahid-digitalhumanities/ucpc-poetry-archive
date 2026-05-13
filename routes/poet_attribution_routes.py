# routes/poet_attribution_routes.py
from flask import Blueprint, request, jsonify
from models.ai_engine.poet_attribution_engine import predict_poet_with_retrieval

attribution_bp = Blueprint('attribution', __name__, url_prefix='/api/attribution')

@attribution_bp.route('/predict', methods=['POST'])
def predict():
    data = request.json
    text = data.get('text', '')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    result = predict_poet_with_retrieval(text)
    return jsonify(result)