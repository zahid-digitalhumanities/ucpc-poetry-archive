# routes/similarity_route.py - Free tier compatible
from flask import Blueprint, render_template, request, abort, jsonify
from models.similarity_model import find_similar_ghazals
from models.ghazal_model import get_ghazal_with_verses
from models.base import get_db_connection
import traceback

similarity_bp = Blueprint('similarity', __name__, url_prefix='/similar')

@similarity_bp.route('/<int:text_id>')
def similar_ghazals(text_id):
    """Display similar ghazals for a given text_id."""
    try:
        result = get_ghazal_with_verses(text_id)
        if not result:
            abort(404)
        
        # Handle different return types from get_ghazal_with_verses
        if isinstance(result, tuple):
            ghazal, verses = result
        else:
            ghazal = result.get('ghazal')
            verses = result.get('verses')
        
        if not ghazal:
            abort(404)
        
        # Find similar ghazals (free tier optimized)
        similar = find_similar_ghazals(text_id, top_n=10)
        
        if similar is None:
            similar = []
        
        similar_details = []
        conn = get_db_connection()
        cur = conn.cursor()
        
        for item in similar:
            tid = item.get('text_id')
            sim = item.get('similarity', 0)
            explanation = item.get('explanation', {})
            
            cur.execute("""
                SELECT t.id, t.title_urdu, t.title_english, p.name as poet_name
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE t.id = %s
            """, (tid,))
            row = cur.fetchone()
            
            if row:
                if isinstance(row, dict):
                    similar_details.append({
                        'id': row['id'],
                        'title_urdu': row.get('title_urdu', ''),
                        'title_english': row.get('title_english', ''),
                        'poet_name': row.get('poet_name', ''),
                        'similarity': sim,
                        'explanation': explanation
                    })
                else:
                    similar_details.append({
                        'id': row[0],
                        'title_urdu': row[1] or '',
                        'title_english': row[2] or '',
                        'poet_name': row[3] or '',
                        'similarity': sim,
                        'explanation': explanation
                    })
        
        cur.close()
        conn.close()
        
        # Return JSON if requested
        if request.args.get('format') == 'json':
            return jsonify(similar_details)
        
        return render_template('similar.html', ghazal=ghazal, similar=similar_details)
    
    except Exception as e:
        traceback.print_exc()
        if request.args.get('format') == 'json':
            return jsonify({'error': str(e), 'message': 'Similarity service temporarily unavailable'}), 500
        abort(500)

@similarity_bp.route('/api/health')
def similarity_health():
    """Health check for similarity endpoint."""
    return jsonify({
        'status': 'healthy',
        'mode': 'keyword-based (free tier optimized)',
        'embeddings_enabled': False
    })
