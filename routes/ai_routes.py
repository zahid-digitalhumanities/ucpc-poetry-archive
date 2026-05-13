# routes/ai_routes_v2.py
"""
Enhanced AI routes for poet prediction and similarity search
"""

from flask import Blueprint, request, jsonify
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.ghazal_model import get_ghazal_with_verses
from models.ai_engine.poet_prediction_ai_v2 import predict_poet_from_text
from models.base import get_db_connection

# Use the similarity model from original or enhanced
try:
    from models.ai_engine.similarity_model import find_similar_ghazals
except ImportError:
    from models.similarity_model import find_similar_ghazals

ai_bp = Blueprint('ai', __name__)

# ===============================
# 🤖 POET PREDICTION API (TEXT INPUT)
# ===============================

@ai_bp.route('/api/ai/predict-poet', methods=['POST'])
def predict_poet_from_text_api():
    """
    Predict poet from provided text
    POST: { "text": "ghazal text here", "top_n": 3 }
    """
    data = request.json or {}
    text = data.get('text', '').strip()
    top_n = data.get('top_n', 3)
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    predictions = predict_poet_from_text(text, top_n=top_n)
    
    if not predictions:
        return jsonify({"error": "Prediction failed"}), 500
    
    return jsonify({
        "success": True,
        "predictions": predictions,
        "top_prediction": predictions[0] if predictions else None
    })

# ===============================
# 🤖 POET PREDICTION API (BY GHAZAL ID)
# ===============================

@ai_bp.route('/api/ai/predict-poet/<int:text_id>')
def predict_poet_by_id(text_id):
    """Predict poet for an existing ghazal by ID"""
    
    result = get_ghazal_with_verses(text_id)
    if not result:
        return jsonify({"error": "Ghazal not found"}), 404
    
    if isinstance(result, tuple):
        ghazal, verses = result
    else:
        ghazal = result.get("ghazal")
        verses = result.get("verses")
    
    if not verses:
        return jsonify({"error": "No verses found"}), 404
    
    # Reconstruct full text from verses
    text = "\n".join([
        f"{v.get('misra1_urdu', '')}\n{v.get('misra2_urdu', '')}"
        for v in verses
    ])
    
    predictions = predict_poet_from_text(text, top_n=3)
    
    if not predictions:
        return jsonify({"error": "No prediction"}), 500
    
    return jsonify({
        "text_id": text_id,
        "predictions": predictions,
        "top_prediction": predictions[0] if predictions else None
    })

# ===============================
# 🔍 SIMILAR GHAZALS API
# ===============================

@ai_bp.route('/api/ai/similar/<int:text_id>')
def similar_ghazals(text_id):
    """Find similar ghazals by embedding similarity"""
    
    similar = find_similar_ghazals(text_id, top_n=10)
    
    if not similar:
        return jsonify([])
    
    # Add titles and poet names to the results
    conn = get_db_connection()
    cur = conn.cursor()
    
    for s in similar:
        cur.execute("SELECT title_urdu, poet_id FROM texts WHERE id = %s", (s['text_id'],))
        row = cur.fetchone()
        if row:
            s['title_urdu'] = row['title_urdu']
            # Get poet name
            cur2 = conn.cursor()
            cur2.execute("SELECT name, name_urdu FROM poets WHERE id = %s", (row['poet_id'],))
            poet_row = cur2.fetchone()
            if poet_row:
                s['poet_name'] = poet_row['name']
                s['poet_name_urdu'] = poet_row['name_urdu']
            cur2.close()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "text_id": text_id,
        "similar_count": len(similar),
        "results": similar
    })

# ===============================
# 📊 BATCH PREDICTION API
# ===============================

@ai_bp.route('/api/ai/batch-predict', methods=['POST'])
def batch_predict():
    """Batch poet prediction for multiple texts"""
    
    data = request.json or {}
    texts = data.get('texts', [])
    
    if not texts:
        return jsonify({"error": "No texts provided"}), 400
    
    from models.ai_engine.poet_prediction_ai_v2 import predict_batch
    
    results = predict_batch(texts, top_n=3)
    
    return jsonify({
        "success": True,
        "count": len(results),
        "results": results
    })

# ===============================
# 🎯 MODEL INFO API
# ===============================

@ai_bp.route('/api/ai/model-info')
def model_info():
    """Get information about the current poet prediction model"""
    
    try:
        from models.ai_engine.poet_prediction_ai_v2 import load_model
        model = load_model()
        
        return jsonify({
            "model_version": "v8",
            "accuracy": model.get('accuracy', 'N/A'),
            "num_poets": model.get('num_poets', 0),
            "training_date": model.get('training_date', 'Unknown'),
            "total_samples": model.get('total_samples', 0),
            "features": model.get('config', {})
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "model_loaded": False
        }), 500

# ===============================
# 🧪 TEST API
# ===============================

@ai_bp.route('/api/ai/test', methods=['POST'])
def test_prediction():
    """Test endpoint with sample ghazals"""
    
    data = request.json or {}
    test_type = data.get('test_type', 'ghalib')
    
    test_ghazals = {
        'ghalib': """
        دل ہی تو ہے نہ سنگ و خشت، درد سے بھر نہ آئے کیوں
        روئیں گے ہم ہزار بار، کوئی ہمیں سزائے کیوں
        """,
        'mir': """
        دل کی کیا خوبی کہ ناداں دل کو سمجھا ہی نہیں
        آگے بجھنا ہے تو بجھ جا، اور جلنا ہے تو جل
        """,
        'faiz': """
        دلِ ناداں تجھے ہوا کیا ہے؟
        آخر اس درد کی دوا کیا ہے؟
        """,
        'iqbal': """
        خودی کو کر بلند اتنا کہ ہر تقدیر سے پہلے
        خدا بندے سے خود پوچھے، بتا تیری رضا کیا ہے
        """,
        'faraz': """
        مجھے تم سے محبت ہے مگر کہنے کی جرأت نہیں
        یہ کیسا عشق ہے جس میں وفا کرنے کی ہمت نہیں
        """
    }
    
    text = test_ghazals.get(test_type, test_ghazals['ghalib'])
    
    predictions = predict_poet_from_text(text, top_n=3)
    
    return jsonify({
        "test_type": test_type,
        "expected": test_type.capitalize(),
        "predictions": predictions
    })