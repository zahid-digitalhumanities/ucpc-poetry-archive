# routes/corpus_routes.py
from flask import Blueprint, render_template, request, jsonify
from models.search_model import search_ghazals, smart_search
from models.base import get_db_connection

corpus_bp = Blueprint('corpus', __name__, url_prefix='/corpus')


def enrich_with_couplet(results):
    """Add 'first_couplet' (misra1<br>misra2) to each result."""
    if not results:
        return
    conn = get_db_connection()
    cur = conn.cursor()
    for r in results:
        tid = r.get('text_id') or r.get('id')
        if not tid:
            continue
        cur.execute("""
            SELECT misra1_urdu, misra2_urdu
            FROM verses
            WHERE text_id = %s AND couplet_index = 1
        """, (tid,))
        row = cur.fetchone()
        if row:
            m1 = row['misra1_urdu'] or ''
            m2 = row['misra2_urdu'] or ''
            if m1 and m2:
                r['first_couplet'] = f"{m1}<br>{m2}"
            elif m1:
                r['first_couplet'] = m1
            else:
                r['first_couplet'] = r.get('title_urdu', '')
        else:
            r['first_couplet'] = r.get('title_urdu', '')
    cur.close()
    conn.close()


@corpus_bp.route('/')
def corpus_page():
    return render_template('corpus.html')


@corpus_bp.route('/api/search')
def corpus_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        results, total = search_ghazals({
            "keyword": q,
            "limit": 20,
            "offset": 0
        })
        enrich_with_couplet(results)   # add full couplet
        return jsonify({
            "results": results,
            "total": total,
            "type": "keyword"
        })
    except Exception as e:
        print("❌ Corpus API error:", e)
        return jsonify({"results": [], "total": 0})


@corpus_bp.route('/api/semantic')
def corpus_semantic():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    try:
        results = smart_search(q, top_n=10)
        if not results:
            return jsonify({"results": [], "type": "semantic"})
        enrich_with_couplet(results)
        return jsonify({
            "results": results,
            "type": "semantic"
        })
    except Exception as e:
        print("❌ Semantic API error:", e)
        return jsonify({"results": []})