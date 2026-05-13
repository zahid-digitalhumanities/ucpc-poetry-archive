from flask import Blueprint, render_template, request, jsonify
from models.search_model import search_ghazals, get_suggestions
from models.ghazal_model import get_stats, get_all_poets, get_all_contributors
from models.stopwords import is_generic_query, suggest_alternative
from modules.search_ranker import score_result
from modules.roman_normalizer import roman_to_urdu, contains_roman

search_bp = Blueprint('search', __name__, url_prefix='/search')

def extract_matla_from_text(text_urdu: str) -> str:
    """Extract first couplet (first 2 lines) from ghazal text."""
    if not text_urdu:
        return ""
    lines = [l.strip() for l in text_urdu.split('\n') if l.strip()]
    if len(lines) >= 2:
        return f"{lines[0]} {lines[1]}"
    elif len(lines) == 1:
        return lines[0]
    return ""

@search_bp.route('/')
def search_page():
    keyword = request.args.get('keyword', '').strip()
    poet_id = request.args.get('poet_id', type=int)
    contributor_id = request.args.get('contributor_id', type=int)
    offset = request.args.get('offset', 0, type=int)
    limit = 20

    # ---- Roman Urdu handling ----
    original_keyword = keyword
    roman_converted = False
    if keyword and contains_roman(keyword):
        keyword = roman_to_urdu(keyword)
        roman_converted = True
        print(f"🔤 Roman conversion: '{original_keyword}' → '{keyword}'")
    # ---------------------------------

    filters = {
        'keyword': keyword,
        'poet_id': poet_id,
        'contributor_id': contributor_id,
        'offset': offset,
        'limit': limit
    }

    generic_warning = None

    if keyword or poet_id or contributor_id:
        results, total = search_ghazals(filters)
        
        # Handle generic query (total == -1 signals generic)
        if total == -1:
            results = []
            total = 0
            generic_warning = f"Query '{keyword}' is too broad. {suggest_alternative(keyword)} Please use at least 3 words or a specific phrase."
        else:
            # ---- Weighted ranking for search results ----
            if results and keyword:
                ranked_results = []
                for r in results:
                    # Try multiple possible field names for matla
                    matla = r.get('matla', '') or r.get('first_couplet', '') or ''
                    
                    # If matla still empty, extract from text_urdu
                    text_urdu = r.get('text_urdu', '') or r.get('full_text', '') or ''
                    if not matla and text_urdu:
                        matla = extract_matla_from_text(text_urdu)
                    
                    # Get full text for phrase matching
                    full_text = text_urdu or r.get('normalized_text', '') or ''
                    
                    # Calculate score based on match type
                    scoring = score_result(keyword, matla, full_text)
                    
                    # Add scoring metadata to result
                    r['match_type'] = scoring['match_type']
                    r['relevance_score'] = scoring['score']
                    
                    # Store matla for display if not already present
                    if not r.get('matla') and matla:
                        r['matla'] = matla
                    
                    ranked_results.append(r)
                
                # Sort by relevance score (highest first)
                ranked_results.sort(key=lambda x: x['relevance_score'], reverse=True)
                results = ranked_results
                
                # Print ranking summary for debugging
                if results:
                    print(f"📊 Search ranking for '{keyword}':")
                    for i, r in enumerate(results[:5]):
                        poet_name = r.get('poet_name', 'Unknown')
                        title = r.get('title_urdu', 'Untitled')[:40]
                        match_type = r.get('match_type', 'unknown')
                        score = r.get('relevance_score', 0)
                        print(f"   {i+1}. [{match_type}] Score: {score} - {poet_name}: {title}")
            # ---------------------------------
    else:
        results, total = [], 0

    data = {
        'stats': get_stats(),
        'poets': get_all_poets(),
        'contributors': get_all_contributors(),
        'results': results,
        'total_results': total,
        'offset': offset,
        'limit': limit,
        'keyword': keyword,
        'original_keyword': original_keyword,
        'poet_id': poet_id,
        'contributor_id': contributor_id,
        'generic_warning': generic_warning,
        'roman_converted': roman_converted
    }
    return render_template('search.html', **data)

@search_bp.route('/suggest')
def suggest():
    q = request.args.get('q', '').strip()
    
    # ---- Roman handling for suggestions ----
    if q and contains_roman(q):
        q = roman_to_urdu(q)
        print(f"🔤 Suggestion Roman conversion: '{q}'")
    # --------------------------------------------
    
    if len(q) < 2:
        return jsonify({'suggestions': []})
    suggestions = get_suggestions(q)
    return jsonify({'suggestions': suggestions})