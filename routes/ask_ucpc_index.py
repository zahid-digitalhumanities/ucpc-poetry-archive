# routes/ask_ucpc_index.py
from flask import Blueprint, request, jsonify
from models.ai_engine.poet_prediction_ai import predict_poet_from_text
from models.ai_engine.similarity_model import find_similar_ghazals
from models.base import get_db_connection
from models.search_model import smart_search
from modules.radif_qaafiya import process_ghazal   # 🔥 ADDED

ask_index_bp = Blueprint('ask_index', __name__, url_prefix='/ask-index')

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

@ask_index_bp.route('/', methods=['POST'])
def ask_ucpc_index():
    data = request.json
    question = data.get('question', '').lower()
    text = data.get('text', '')

    if not text.strip():
        return jsonify({'error': 'No text provided'}), 400

    try:
        # 1. Ask about poet
        if any(word in question for word in ['poet', 'kis', 'author', 'likhi']):
            predictions = predict_poet_from_text(text, top_n=3)
            if not predictions:
                return jsonify({'type': 'poet', 'data': []})
            for p in predictions:
                name, name_urdu = get_poet_name(p['poet_id'])
                p['poet_name'] = name
                p['poet_name_urdu'] = name_urdu
            return jsonify({'type': 'poet', 'data': predictions})

        # 2. Ask about theme
        elif 'theme' in question:
            text_lower = text.lower()
            love_words = ['عشق', 'محبت', 'دل', 'یار', 'غم', 'وفا', 'یاد']
            if any(w in text_lower for w in love_words):
                theme = "Love / Grief"
                reason = "Words like عشق, محبت, غم detected"
            else:
                theme = "General"
                reason = "No strong emotional keywords found"
            return jsonify({
                'type': 'theme',
                'data': {'theme': theme, 'reason': reason}
            })

        # 3. Ask about Radif / Qaafiya (NEW)
        elif any(word in question for word in ['radif', 'qaafiya', 'rhyme', 'refrain']):
            try:
                # Call process_ghazal (dummy text_id, as it's not used for extraction)
                result = process_ghazal(0, text)
                radif = result.get('radif')
                qaafiya = result.get('qaafiya') or []
                confidence = result.get('confidence', 0.0)
                return jsonify({
                    'type': 'radif',
                    'data': {
                        'radif': radif,
                        'qaafiya': qaafiya,
                        'confidence': confidence
                    }
                })
            except Exception as e:
                return jsonify({'type': 'radif', 'data': {'error': str(e)}})

        # 4. Semantic search for ghazals by meaning
        elif any(word in question for word in ['ghazal', 'search', 'like', 'similar', 'find', 'dhundho']):
            results = smart_search(question, top_n=5)
            if not results:
                return jsonify({'type': 'search', 'data': []})
            return jsonify({'type': 'search', 'data': results})

        else:
            return jsonify({
                'type': 'unknown',
                'data': 'Try asking: "poet name?", "theme?", "radif qaafiya?", or "similar ghazals?"'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500