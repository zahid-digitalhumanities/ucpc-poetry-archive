from flask import Blueprint, request, jsonify
from models.ai_engine.poet_prediction_ai import predict_poet_from_text
from models.ai_engine.similarity_model import find_similar_ghazals
from models.ghazal_model import get_ghazal_with_verses
from models.base import get_db_connection

ask_bp = Blueprint('ask', __name__, url_prefix='/ask')

def get_ghazal_text(text_id):
    result = get_ghazal_with_verses(text_id)
    if not result or not result[0]:
        return None
    ghazal, verses = result
    full_text = " ".join([f"{v.get('misra1_urdu','')} {v.get('misra2_urdu','')}" for v in verses])
    return full_text

def get_poet_name(poet_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name, name_urdu FROM poets WHERE id = %s", (poet_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row['name'], row['name_urdu']
    return "Unknown", ""

@ask_bp.route('/', methods=['POST'])
def ask_ucpc():
    data = request.json
    question = data.get('question', '').lower()
    text_id = data.get('text_id')

    if not text_id:
        return jsonify({'error': 'No text_id provided'}), 400

    ghazal_text = get_ghazal_text(text_id)
    if not ghazal_text:
        return jsonify({'error': 'Ghazal not found'}), 404

    try:
        # 1. Ask about poet
        if any(word in question for word in ['poet', 'kis', 'author']):
            predictions = predict_poet_from_text(ghazal_text, top_n=3)
            if not predictions:
                return jsonify({'type': 'poet_prediction', 'data': []})
            for p in predictions:
                name, name_urdu = get_poet_name(p['poet_id'])
                p['poet_name'] = name
                p['poet_name_urdu'] = name_urdu
            return jsonify({'type': 'poet_prediction', 'data': predictions})

        # 2. Ask about similar ghazals
        elif 'similar' in question:
            similar = find_similar_ghazals(text_id, top_n=5)
            conn = get_db_connection()
            cur = conn.cursor()
            for s in similar:
                cur.execute("SELECT title_urdu, poet_id FROM texts WHERE id = %s", (s['text_id'],))
                row = cur.fetchone()
                if row:
                    s['title_urdu'] = row['title_urdu']
                    poet_name, _ = get_poet_name(row['poet_id'])
                    s['poet_name'] = poet_name
            cur.close()
            conn.close()
            return jsonify({'type': 'similar', 'data': similar})

        # 3. Ask about theme / explainable
        elif any(word in question for word in ['theme', 'topic', 'subject']):
            similar = find_similar_ghazals(text_id, top_n=1)
            if similar:
                breakdown = similar[0].get('explanation', {}).get('breakdown', {})
                theme_score = breakdown.get('theme', 0)
                theme = "Love/Grief" if theme_score > 0 else "General"
                reason = "Based on keyword patterns and thematic similarity."
            else:
                theme = "Could not determine"
                reason = "Not enough data"
            return jsonify({
                'type': 'theme',
                'data': {'theme': theme, 'reason': reason}
            })

        else:
            return jsonify({
                'type': 'unknown',
                'data': 'Try asking "Who is the poet?", "Show similar ghazals", or "What is the theme?"'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500