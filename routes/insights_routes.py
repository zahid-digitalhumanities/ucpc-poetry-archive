from flask import Blueprint, render_template, request, flash
from flask import Blueprint, render_template, jsonify
from models.base import get_db_connection
from collections import Counter
import json
import os
import re
import traceback

insights_bp = Blueprint('insights', __name__, url_prefix='/insights')
def get_poets():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, name_urdu FROM poets ORDER BY name")
    poets = [dict(row) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return poets
@insights_bp.route('/model-performance')
def model_performance():
    """Display model performance dashboard."""
    metrics_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'model_metrics.json')
    if not os.path.exists(metrics_file):
        return "Metrics not available. Run python scripts/compute_model_metrics.py first.", 404
    
    with open(metrics_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return render_template('model_performance.html', metrics=data)

@insights_bp.route('/top-radif')
def top_radif():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT radif FROM poetic_features WHERE radif IS NOT NULL AND radif != ''")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        radif_list = [r['radif'].strip() for r in rows]
        top_radif = Counter(radif_list).most_common(20)
        total_ghazals = len(radif_list)
        return render_template('insights/top_radif.html', top_radif=top_radif, total_ghazals=total_ghazals)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@insights_bp.route('/poet-words', methods=['GET', 'POST'])
def poet_words():
    try:
        poets = get_poets()
        selected_poet = request.args.get('poet') or (request.form.get('poet') if request.method == 'POST' else None)
        top_words = []
        poet_name_display = ""
        if selected_poet:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT t.text_urdu
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE p.name = %s AND t.text_urdu IS NOT NULL
            """, (selected_poet,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            word_counter = Counter()
            for row in rows:
                text = row['text_urdu'] or ''
                tokens = re.findall(r'[\u0600-\u06FF]+', text)
                word_counter.update(tokens)
            top_words = word_counter.most_common(20)
            poet_name_display = selected_poet
        return render_template('insights/poet_words.html', poets=poets, selected_poet=selected_poet, top_words=top_words, poet_name_display=poet_name_display)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500

@insights_bp.route('/poet-emotions', methods=['GET', 'POST'])
def poet_emotions():
    try:
        poets = get_poets()
        selected_poet = request.args.get('poet') or (request.form.get('poet') if request.method == 'POST' else None)
        emotion_counts = None
        poet_name_display = ""
        if selected_poet:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT t.text_urdu
                FROM texts t
                JOIN poets p ON t.poet_id = p.id
                WHERE p.name = %s AND t.text_urdu IS NOT NULL
            """, (selected_poet,))
            rows = cur.fetchall()
            cur.close()
            conn.close()
            emotion_dict = {
                "love": ["محبت", "عشق", "دل", "آرزو", "دیدار", "وصل"],
                "sadness": ["غم", "درد", "تنہائی", "اشک", "فراق", "ہجر"],
                "hope": ["امید", "روشنی", "خوشی", "آزادی", "سحر"]
            }
            emotion_counts = {"love": 0, "sadness": 0, "hope": 0}
            for row in rows:
                text = row['text_urdu'] or ''
                for emotion, keywords in emotion_dict.items():
                    for kw in keywords:
                        if kw in text:
                            emotion_counts[emotion] += 1
                            break
            poet_name_display = selected_poet
        return render_template('insights/poet_emotions.html', poets=poets, selected_poet=selected_poet, emotion_counts=emotion_counts, poet_name_display=poet_name_display)
    except Exception as e:
        traceback.print_exc()
        return f"Error: {str(e)}", 500
# ------------------- 4. Meter Clusters -------------------
@insights_bp.route('/meter-clusters')
def meter_clusters():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT pattern, frequency, example_text_id FROM meter_patterns ORDER BY frequency DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    patterns = [{'pattern': r['pattern'], 'frequency': r['frequency'], 'example_id': r['example_text_id']} for r in rows]
    return render_template('insights/meter_clusters.html', patterns=patterns)

# ------------------- 5. Compare Poets -------------------
@insights_bp.route('/compare-poets', methods=['GET', 'POST'])
def compare_poets():
    poets = get_poets()
    poet1 = None
    poet2 = None
    stats1 = {}
    stats2 = {}
    if request.method == 'POST':
        poet1_name = request.form.get('poet1')
        poet2_name = request.form.get('poet2')
        if poet1_name and poet2_name:
            poet1 = next((p for p in poets if p['name'] == poet1_name), None)
            poet2 = next((p for p in poets if p['name'] == poet2_name), None)
            stats1 = get_poet_stats(poet1_name)
            stats2 = get_poet_stats(poet2_name)
    return render_template('insights/compare_poets.html', poets=poets, poet1=poet1, poet2=poet2, stats1=stats1, stats2=stats2)

def get_poet_stats(poet_name):
    conn = get_db_connection()
    cur = conn.cursor()
    # Word frequencies (top 10)
    cur.execute("""
        SELECT word, COUNT(*) as freq
        FROM (
            SELECT unnest(regexp_matches(t.text_urdu, '[\u0600-\u06FF]+', 'g')) as word
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE p.name = %s AND t.text_urdu IS NOT NULL
        ) words
        GROUP BY word
        ORDER BY freq DESC
        LIMIT 10
    """, (poet_name,))
    top_words = [dict(row) for row in cur.fetchall()]
    # Radif distribution (top 5)
    cur.execute("""
        SELECT pf.radif, COUNT(*) as count
        FROM poetic_features pf
        JOIN texts t ON pf.text_id = t.id
        JOIN poets p ON t.poet_id = p.id
        WHERE p.name = %s AND pf.radif IS NOT NULL
        GROUP BY pf.radif
        ORDER BY count DESC
        LIMIT 5
    """, (poet_name,))
    top_radif = [dict(row) for row in cur.fetchall()]
    # Emotion counts
    emotion_counts = {"love": 0, "sadness": 0, "hope": 0}
    cur.execute("SELECT t.text_urdu FROM texts t JOIN poets p ON t.poet_id = p.id WHERE p.name = %s AND t.text_urdu IS NOT NULL", (poet_name,))
    rows = cur.fetchall()
    emotion_dict = {
        "love": ["محبت", "عشق", "دل", "آرزو", "دیدار", "وصل"],
        "sadness": ["غم", "درد", "تنہائی", "اشک", "فراق", "ہجر"],
        "hope": ["امید", "روشنی", "خوشی", "آزادی", "سحر"]
    }
    for row in rows:
        text = row['text_urdu'] or ''
        for emotion, keywords in emotion_dict.items():
            for kw in keywords:
                if kw in text:
                    emotion_counts[emotion] += 1
                    break
    cur.close()
    conn.close()
    return {
        'top_words': top_words,
        'top_radif': top_radif,
        'emotions': emotion_counts
    }

# ------------------- 6. Enhanced Search -------------------
@insights_bp.route('/advanced-search', methods=['GET', 'POST'])
def advanced_search():
    poets = get_poets()
    results = []
    query = {}
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        radif = request.form.get('radif', '').strip()
        qaafiya = request.form.get('qaafiya', '').strip()
        meter = request.form.get('meter', '').strip()
        theme = request.form.get('theme', '').strip()
        poet_id = request.form.get('poet_id', type=int)
        query = {'keyword': keyword, 'radif': radif, 'qaafiya': qaafiya, 'meter': meter, 'theme': theme, 'poet_id': poet_id}

        conn = get_db_connection()
        cur = conn.cursor()
        sql = """
            SELECT t.id, t.title_urdu, t.title_english, p.name as poet_name,
                   pf.radif, pf.qaafiya, pf.meter, pf.theme,
                   ts_rank(t.search_vector, plainto_tsquery('simple', %s)) as rank
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            LEFT JOIN poetic_features pf ON t.id = pf.text_id
            WHERE 1=1
        """
        params = []
        # Full‑text search on keyword
        if keyword:
            sql += " AND t.search_vector @@ plainto_tsquery('simple', %s)"
            params.append(keyword)
        else:
            # If no keyword, we still need a dummy rank for ordering (e.g., by id)
            sql += " AND 1=1"
        # Other filters (unchanged)
        if radif:
            sql += " AND pf.radif = %s"
            params.append(radif)
        if qaafiya:
            sql += " AND %s = ANY(pf.qaafiya)"
            params.append(qaafiya)
        if meter:
            sql += " AND pf.meter = %s"
            params.append(meter)
        if theme:
            sql += " AND pf.theme = %s"
            params.append(theme)
        if poet_id:
            sql += " AND t.poet_id = %s"
            params.append(poet_id)
        # Order by relevance if keyword provided, otherwise by id
        if keyword:
            sql += " ORDER BY rank DESC"
        else:
            sql += " ORDER BY t.id"
        sql += " LIMIT 50"
        cur.execute(sql, params)
        rows = cur.fetchall()
        results = [dict(row) for row in rows]
        cur.close()
        conn.close()
    return render_template('insights/advanced_search.html', results=results, query=query, poets=poets)