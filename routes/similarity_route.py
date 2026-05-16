from flask import Blueprint, render_template, request, abort, jsonify
from models.similarity_model import find_similar_ghazals
from models.ghazal_model import get_ghazal_with_verses
from models.base import get_db_connection
import traceback

similarity_bp = Blueprint('similarity', __name__, url_prefix='/similar')

@similarity_bp.route('/<int:text_id>')
def similar_ghazals(text_id):
    try:
        result = get_ghazal_with_verses(text_id)
        if not result or not result[0]:
            abort(404)
        ghazal, _ = result

        similar = find_similar_ghazals(text_id, top_n=10)
        if similar is None:
            similar = []

        similar_details = []
        conn = get_db_connection()
        cur = conn.cursor()

        for item in similar:
            tid = item['text_id']
            sim = item['similarity']
            explanation = item['explanation']   # dict with embedding_score, breakdown, explanation_text

            cur.execute("""
                SELECT t.id, t.title_urdu, t.title_english, p.name as poet_name
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE t.id = %s
            """, (tid,))
            row = cur.fetchone()
            if row:
                similar_details.append({
                    'id': row['id'],
                    'title_urdu': row['title_urdu'],
                    'title_english': row['title_english'],
                    'poet_name': row['poet_name'],
                    'similarity': sim,
                    'explanation': explanation
                })

        cur.close()
        conn.close()

        if request.args.get('format') == 'json':
            return jsonify(similar_details)

        return render_template('similar.html', ghazal=ghazal, similar=similar_details)

    except Exception as e:
        traceback.print_exc()
        if request.args.get('format') == 'json':
            return jsonify({'error': str(e)}), 500
        abort(500)