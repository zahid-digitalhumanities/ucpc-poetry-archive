# routes/ask_ucpc_route.py
from flask import Blueprint, request, jsonify
from models.ghazal_model import get_ghazal_with_verses
from models.ai_engine.similarity_model import find_similar_ghazals
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

def get_first_couplet_html(text_id):
    """Return HTML string: misra1_urdu<br>misra2_urdu or empty string."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT misra1_urdu, misra2_urdu
        FROM verses
        WHERE text_id = %s AND couplet_index = 1
    """, (text_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        m1 = row['misra1_urdu'] or ''
        m2 = row['misra2_urdu'] or ''
        if m1 and m2:
            return f"{m1}<br>{m2}"
        return m1 or m2
    return ""

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
            from models.ai_engine.poet_prediction_ai import predict_poet_from_text
            predictions = predict_poet_from_text(ghazal_text, top_n=3)
            if not predictions:
                return jsonify({'type': 'poet_prediction', 'data': []})
            for p in predictions:
                name, name_urdu = get_poet_name(p['poet_id'])
                p['poet_name'] = name
                p['poet_name_urdu'] = name_urdu
            return jsonify({'type': 'poet_prediction', 'data': predictions})

        # 2. Ask about similar ghazals (with full couplet)
        elif 'similar' in question:
            similar = find_similar_ghazals(text_id, top_n=5)
            if not similar:
                return jsonify({'type': 'similar', 'data': []})

            conn = get_db_connection()
            cur = conn.cursor()
            for s in similar:
                tid = s['text_id']
                cur.execute("""
                    SELECT t.title_urdu, p.name as poet_name
                    FROM texts t
                    JOIN poets p ON t.poet_id = p.id
                    WHERE t.id = %s
                """, (tid,))
                row = cur.fetchone()
                if row:
                    s['title_urdu'] = row['title_urdu']
                    s['poet_name'] = row['poet_name']
                s['first_couplet'] = get_first_couplet_html(tid)
            cur.close()
            conn.close()
            return jsonify({'type': 'similar', 'data': similar})

        # 3. Ask about theme
        elif any(word in question for word in ['theme', 'topic', 'subject']):
            # Simple keyword detection – you can upgrade later
            text_lower = ghazal_text.lower()
            love_words = ['عشق', 'محبت', 'دل', 'یار', 'غم', 'وفا', 'یاد']
            detected = [w for w in love_words if w in text_lower]
            if detected:
                theme = "Love / Grief"
                reason = f"Words like {', '.join(detected[:3])} detected"
            else:
                theme = "General"
                reason = "No strong emotional keywords found"
            return jsonify({
                'type': 'theme',
                'data': {
                    'theme': theme,
                    'reason': reason,
                    'keywords': detected
                }
            })

        # 4. Ask about radif / qaafiya
        elif any(word in question for word in ['radif', 'qaafiya', 'rhyme', 'refrain']):
            from modules.radif_qaafiya import process_ghazal
            try:
                result = process_ghazal(text_id, ghazal_text)
                return jsonify({
                    'type': 'radif',
                    'data': {
                        'radif': result.get('radif'),
                        'qaafiya': result.get('qaafiya'),
                        'confidence': result.get('confidence', 0.0)
                    }
                })
            except Exception as e:
                return jsonify({'type': 'radif', 'data': {'error': str(e)}})

        else:
            return jsonify({
                'type': 'unknown',
                'data': 'Try asking: "Who is the poet?", "Similar ghazals?", "What is the theme?", or "Radif Qaafiya?"'
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500