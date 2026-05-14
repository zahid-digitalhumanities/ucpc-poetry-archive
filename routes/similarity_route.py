"""
Similar Ghazals Route - Lightweight version for free tier
Uses database-based similarity (keyword matching) instead of semantic embeddings
"""

from flask import Blueprint, jsonify, request, render_template
import re
from collections import Counter

similarity_bp = Blueprint('similarity', __name__, url_prefix='/similarity')

def normalize_urdu(text):
    """Basic Urdu normalization."""
    if not text:
        return ""
    text = str(text)
    replacements = {'ي': 'ی', 'ك': 'ک', 'ة': 'ہ', 'أ': 'ا', 'إ': 'ا'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(text, top_n=10):
    """Extract important keywords from text."""
    words = normalize_urdu(text).split()
    # Remove short words (likely not meaningful)
    keywords = [w for w in words if len(w) > 1]
    # Count frequency
    freq = Counter(keywords)
    return [word for word, count in freq.most_common(top_n)]

def calculate_similarity(text1, text2):
    """Calculate simple similarity score based on keyword overlap."""
    if not text1 or not text2:
        return 0.0
    
    keywords1 = set(extract_keywords(text1, 15))
    keywords2 = set(extract_keywords(text2, 15))
    
    if not keywords1 or not keywords2:
        return 0.0
    
    intersection = keywords1.intersection(keywords2)
    union = keywords1.union(keywords2)
    
    if not union:
        return 0.0
    
    # Jaccard similarity
    similarity = len(intersection) / len(union)
    
    # Bonus for same poet (often similar style)
    return round(similarity, 4)

def get_ghazal_matla(text_id):
    """Get ghazal matla (first couplet) from database."""
    from models.base import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.id, t.matla, t.title_urdu, p.name as poet_name
        FROM texts t
        JOIN poets p ON t.poet_id = p.id
        WHERE t.id = %s AND t.form = 'ghazal'
    """, (text_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if row:
        if isinstance(row, dict):
            return {
                'id': row['id'],
                'matla': row['matla'] or '',
                'title': row['title_urdu'] or '',
                'poet': row['poet_name']
            }
        else:
            return {
                'id': row[0],
                'matla': row[1] or '',
                'title': row[2] or '',
                'poet': row[3]
            }
    return None

def get_similar_ghazals_db(text_id, target_text, poet_name=None, limit=10):
    """Find similar ghazals using database and keyword matching."""
    from models.base import get_db_connection
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get all ghazals except the current one
    if poet_name:
        # Prefer same poet first
        cur.execute("""
            SELECT t.id, t.matla, t.title_urdu, p.name as poet_name, t.text_urdu
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.form = 'ghazal' 
            AND t.id != %s
            AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
            ORDER BY CASE WHEN p.name = %s THEN 0 ELSE 1 END
            LIMIT 50
        """, (text_id, poet_name))
    else:
        cur.execute("""
            SELECT t.id, t.matla, t.title_urdu, p.name as poet_name, t.text_urdu
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.form = 'ghazal' 
            AND t.id != %s
            AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
            LIMIT 50
        """, (text_id,))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    # Calculate similarity for each ghazal
    results = []
    target_keywords = extract_keywords(target_text, 20)
    
    for row in rows:
        if isinstance(row, dict):
            ghazal_text = row.get('text_urdu', '') or row.get('matla', '')
            ghazal_poet = row.get('poet_name', '')
            ghazal_id = row.get('id')
            ghazal_matla = row.get('matla', '')
            ghazal_title = row.get('title_urdu', '')
        else:
            ghazal_id = row[0]
            ghazal_matla = row[1] or ''
            ghazal_title = row[2] or ''
            ghazal_poet = row[3]
            ghazal_text = row[4] or ghazal_matla
        
        if not ghazal_text:
            ghazal_text = ghazal_matla
        
        # Calculate similarity score
        similarity = calculate_similarity(target_text, ghazal_text)
        
        # Bonus for same poet
        if ghazal_poet == poet_name:
            similarity += 0.15
        
        results.append({
            'id': ghazal_id,
            'matla': ghazal_matla[:150] + '...' if len(ghazal_matla) > 150 else ghazal_matla,
            'title': ghazal_title or 'Untitled',
            'poet': ghazal_poet,
            'similarity_score': round(min(similarity, 1.0), 4)
        })
    
    # Sort by similarity score (highest first)
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    return results[:limit]


@similarity_bp.route('/')
def similarity_home():
    """Render similarity search page."""
    return render_template('similarity.html')


@similarity_bp.route('/api/similar-to/<int:text_id>', methods=['GET'])
def similar_to_ghazal(text_id):
    """API endpoint to find similar ghazals by ID."""
    try:
        # Get the target ghazal
        target = get_ghazal_matla(text_id)
        if not target:
            return jsonify({'error': 'Ghazal not found'}), 404
        
        # Get similar ghazals
        similar = get_similar_ghazals_db(
            text_id, 
            target.get('matla', ''), 
            target.get('poet', ''),
            limit=10
        )
        
        return jsonify({
            'success': True,
            'source_ghazal': target,
            'similar_ghazals': similar,
            'count': len(similar),
            'note': 'Using lightweight keyword-based similarity (free tier optimized)'
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@similarity_bp.route('/api/find-similar', methods=['POST'])
def find_similar():
    """API endpoint to find similar ghazals by text input."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Get similar ghazals
        from models.base import get_db_connection
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.matla, t.title_urdu, p.name as poet_name, t.text_urdu
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.form = 'ghazal' 
            AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
            LIMIT 100
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        
        results = []
        for row in rows:
            if isinstance(row, dict):
                ghazal_text = row.get('text_urdu', '') or row.get('matla', '')
                ghazal_poet = row.get('poet_name', '')
                ghazal_id = row.get('id')
                ghazal_matla = row.get('matla', '')
                ghazal_title = row.get('title_urdu', '')
            else:
                ghazal_id = row[0]
                ghazal_matla = row[1] or ''
                ghazal_title = row[2] or ''
                ghazal_poet = row[3]
                ghazal_text = row[4] or ghazal_matla
            
            similarity = calculate_similarity(text, ghazal_text)
            
            if similarity > 0.1:  # Only include somewhat similar
                results.append({
                    'id': ghazal_id,
                    'matla': ghazal_matla[:150] + '...' if len(ghazal_matla) > 150 else ghazal_matla,
                    'title': ghazal_title or 'Untitled',
                    'poet': ghazal_poet,
                    'similarity_score': round(similarity, 4)
                })
        
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return jsonify({
            'success': True,
            'query_text': text[:200],
            'similar_ghazals': results[:10],
            'count': len(results[:10]),
            'note': 'Using lightweight keyword-based similarity'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@similarity_bp.route('/api/stats', methods=['GET'])
def similarity_stats():
    """Get similarity engine statistics."""
    return jsonify({
        'engine': 'Keyword-based similarity (free tier optimized)',
        'method': 'Jaccard similarity on extracted keywords',
        'status': 'active',
        'memory_usage': 'Low (< 50 MB)',
        'semantic_search': 'Disabled (free tier)'
    })
