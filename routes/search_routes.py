from flask import Blueprint, render_template, request
from models.base import get_db_connection

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
def search_page():
    keyword = request.args.get('keyword', '').strip()
    poet_id = request.args.get('poet_id', type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = 20
    
    results = []
    total = 0
    
    if keyword:
        conn = get_db_connection()
        cur = conn.cursor()
        
        search_term = f"%{keyword}%"
        
        # Build query
        query = """
            SELECT DISTINCT t.id, t.title_urdu, t.text_urdu,
                   p.name as poet_name, p.name_urdu as poet_name_urdu,
                   (SELECT misra1_urdu FROM verses WHERE text_id = t.id AND couplet_index = 1 LIMIT 1) as misra1,
                   (SELECT misra2_urdu FROM verses WHERE text_id = t.id AND couplet_index = 1 LIMIT 1) as misra2
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.form = 'ghazal'
              AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
              AND (t.title_urdu ILIKE %s OR t.text_urdu ILIKE %s OR p.name ILIKE %s)
        """
        params = [search_term, search_term, search_term]
        
        if poet_id:
            query += " AND t.poet_id = %s"
            params.append(poet_id)
        
        query += " ORDER BY t.id DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        # Get total count
        count_query = """
            SELECT COUNT(DISTINCT t.id) as total
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.form = 'ghazal'
              AND (t.is_deleted = FALSE OR t.is_deleted IS NULL)
              AND (t.title_urdu ILIKE %s OR t.text_urdu ILIKE %s OR p.name ILIKE %s)
        """
        count_params = [search_term, search_term, search_term]
        if poet_id:
            count_query += " AND t.poet_id = %s"
            count_params.append(poet_id)
        
        cur.execute(count_query, count_params)
        total = cur.fetchone()['total']
        
        cur.close()
        conn.close()
    
    # Get poets list for filter dropdown
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM poets ORDER BY name")
    poets = cur.fetchall()
    cur.close()
    conn.close()
    
    return render_template('search.html', 
                         results=results, 
                         total=total,
                         keyword=keyword,
                         poet_id=poet_id,
                         poets=poets,
                         offset=offset,
                         limit=limit)
