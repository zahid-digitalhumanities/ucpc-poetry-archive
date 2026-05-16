from flask import Blueprint, render_template
from modules.fingerprint import predict_poet
from models.ghazal_model import get_ghazal_with_verses
from models.base import get_db_connection

fingerprint_bp = Blueprint('fingerprint', __name__, url_prefix='/fingerprint')

@fingerprint_bp.route('/predict/<int:text_id>')
def predict(text_id):
    result = get_ghazal_with_verses(text_id)
    if not result or not result[0]:
        return "Ghazal not found", 404
    ghazal, _ = result
    predictions = predict_poet(text_id)

    conn = get_db_connection()
    cur = conn.cursor()
    enriched = []
    for p in predictions:
        cur.execute("SELECT name, name_urdu FROM poets WHERE id = %s", (p['poet_id'],))
        row = cur.fetchone()
        if row:
            enriched.append({
                'id': p['poet_id'],
                'name': row['name'],
                'name_urdu': row['name_urdu'],
                'similarity': round(p['hybrid_similarity'], 3),
                'components': p['components']
            })
    cur.close()
    conn.close()

    return render_template('predict.html', ghazal=ghazal, predictions=enriched)