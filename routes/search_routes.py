# routes/search_routes.py
from flask import Blueprint, render_template, request, jsonify
from models.search_model import (
    search_ghazals, get_suggestions, get_stats,
    get_all_poets, get_all_contributors
)

search_bp = Blueprint('search', __name__, url_prefix='/search')

@search_bp.route('/')
def search_page():
    keyword = request.args.get('keyword', '').strip()
    poet_id = request.args.get('poet_id', type=int)
    contributor_id = request.args.get('contributor_id', type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = 20

    filters = {
        'keyword': keyword,
        'poet_id': poet_id,
        'contributor_id': contributor_id,
        'offset': offset,
        'limit': limit
    }

    results, total = search_ghazals(filters) if (keyword or poet_id or contributor_id) else ([], 0)

    data = {
        'stats': get_stats(),
        'poets': get_all_poets(),
        'contributors': get_all_contributors(),
        'results': results,
        'total_results': total,
        'offset': offset,
        'limit': limit,
        'keyword': keyword,
        'poet_id': poet_id,
        'contributor_id': contributor_id
    }
    return render_template('search.html', **data)

@search_bp.route('/suggest')
def suggest():
    q = request.args.get('q', '')
    if len(q) < 2:
        return jsonify({'suggestions': []})
    suggestions = get_suggestions(q)
    return jsonify({'suggestions': suggestions})