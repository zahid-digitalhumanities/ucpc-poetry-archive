# modules/explainability.py
from models.base import get_db_connection
from modules.embeddings import get_similarity_score

WEIGHTS = {
    "semantic": 0.5,
    "radif": 0.2,
    "qaafiya": 0.2,
    "theme": 0.1
}

def get_features(conn, text_id):
    cur = conn.cursor()
    cur.execute("""
        SELECT radif, qaafiya, theme
        FROM poetic_features
        WHERE text_id = %s
    """, (text_id,))
    pf = cur.fetchone()
    cur.close()
    return {
        "radif": pf['radif'] if pf else None,
        "qaafiya": pf['qaafiya'] if pf else [],
        "theme": pf['theme'] if pf else None
    }

def match_radif(r1, r2):
    return r1 and r2 and r1 == r2

def match_theme(t1, t2):
    return t1 and t2 and t1 == t2

def match_qaafiya(q1, q2):
    if not q1 or not q2:
        return 0
    overlap = set(q1).intersection(set(q2))
    return len(overlap) / max(len(q1), len(q2))

def explain_similarity(text_id_1, text_id_2):
    conn = get_db_connection()
    try:
        f1 = get_features(conn, text_id_1)
        f2 = get_features(conn, text_id_2)

        semantic_score = get_similarity_score(text_id_1, text_id_2)

        radif_match = match_radif(f1["radif"], f2["radif"])
        theme_match = match_theme(f1["theme"], f2["theme"])
        qaafiya_score = match_qaafiya(f1["qaafiya"], f2["qaafiya"])

        semantic_contrib = semantic_score * WEIGHTS["semantic"]
        radif_contrib = (1 if radif_match else 0) * WEIGHTS["radif"]
        theme_contrib = (1 if theme_match else 0) * WEIGHTS["theme"]
        qaafiya_contrib = qaafiya_score * WEIGHTS["qaafiya"]

        final_score = semantic_contrib + radif_contrib + qaafiya_contrib + theme_contrib

        explanation = []
        explanation.append(f"Semantic similarity ({semantic_score:.2f}) → {semantic_contrib*100:.1f}%")
        if radif_match:
            explanation.append(f"Same radif '{f1['radif']}' → {WEIGHTS['radif']*100:.0f}%")
        else:
            explanation.append("Different radif → 0%")
        if qaafiya_score > 0:
            explanation.append(f"Qaafiya overlap ({qaafiya_score:.2f}) → {qaafiya_contrib*100:.1f}%")
        else:
            explanation.append("No qaafiya overlap → 0%")
        if theme_match:
            explanation.append(f"Same theme '{f1['theme']}' → {WEIGHTS['theme']*100:.0f}%")
        else:
            explanation.append("Different theme → 0%")

        return {
            "score": round(final_score, 3),
            "percentage": round(final_score * 100, 2),
            "breakdown": {
                "semantic": round(semantic_contrib, 3),
                "radif": round(radif_contrib, 3),
                "qaafiya": round(qaafiya_contrib, 3),
                "theme": round(theme_contrib, 3)
            },
            "explanation": explanation
        }
    finally:
        conn.close()