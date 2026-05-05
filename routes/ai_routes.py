# routes/ai_routes.py
from flask import Blueprint, jsonify
from models.ghazal_model import get_ghazal_with_verses
from models.ai_engine.poet_prediction_ai import predict_poet_from_text
from models.ai_engine.similarity_model import find_similar_ghazals
from models.base import get_db_connection

ai_bp = Blueprint('ai', __name__)

# ===============================
# 🤖 POET PREDICTION API
# ===============================
@ai_bp.route('/api/ai/predict-poet/<int:text_id>')
def predict_poet(text_id):
    result = get_ghazal_with_verses(text_id)
    if not result:
        return jsonify({"error": "Ghazal not found"}), 404

    if isinstance(result, tuple):
        ghazal, verses = result
    else:
        ghazal = result.get("ghazal")
        verses = result.get("verses")

    # Reconstruct full text from verses
    text = "\n".join([
        f"{v.get('misra1_urdu','')} {v.get('misra2_urdu','')}"
        for v in verses
    ])

    predictions = predict_poet_from_text(text, top_n=3)
    if not predictions:
        return jsonify({"error": "No prediction"}), 500

    # Return only the top prediction (as a single object)
    top = predictions[0]
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, name_urdu FROM poets WHERE id = %s", (top['poet_id'],))
    poet = cur.fetchone()
    cur.close()
    conn.close()

    return jsonify({
        "poet_id": top['poet_id'],
        "poet_name": poet['name'] if poet else "Unknown",
        "poet_name_urdu": poet['name_urdu'] if poet else "",
        "confidence": top['confidence']
    })

# ===============================
# 🔍 SIMILAR GHAZALS API
# ===============================
@ai_bp.route('/api/ai/similar/<int:text_id>')
def similar(text_id):
    similar = find_similar_ghazals(text_id, top_n=5)
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
            cur2 = conn.cursor()
            cur2.execute("SELECT name FROM poets WHERE id = %s", (row['poet_id'],))
            poet_row = cur2.fetchone()
            s['poet'] = poet_row['name'] if poet_row else "Unknown"
            cur2.close()
    cur.close()
    conn.close()

    return jsonify(similar)