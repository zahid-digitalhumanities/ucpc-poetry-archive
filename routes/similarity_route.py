# routes/similarity_route.py
from flask import Blueprint, render_template, request, abort, jsonify
from models.ai_engine.similarity_model import find_similar_ghazals   # ✅ fixed import
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

        similar = find_similar_ghazals(text_id) or []

        conn = get_db_connection()
        cur = conn.cursor()

        similar_details = []

        for item in similar:
            tid = item.get('text_id')
            sim = item.get('similarity', 0)

            explanation = item.get('explanation', {})
            breakdown = explanation.get('breakdown', {})

            # 🔥 HARD FIX (ensure keys exist)
            breakdown.setdefault('radif', 0)
            breakdown.setdefault('qaafiya', 0)
            breakdown.setdefault('theme', 0)
            breakdown.setdefault('meter', 0)

            explanation['breakdown'] = breakdown

            cur.execute("""
                SELECT t.id, t.title_urdu, t.title_english, p.name as poet_name
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE t.id = %s
            """, (tid,))
            row = cur.fetchone()

            if row:
                similar_details.append({
                    "id": row['id'],
                    "title_urdu": row['title_urdu'],
                    "title_english": row['title_english'],
                    "poet_name": row['poet_name'],
                    "similarity": sim,
                    "explanation": explanation
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