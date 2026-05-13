from flask import Blueprint, jsonify
from models.base import get_db_connection
import json
import numpy as np
from collections import Counter, defaultdict

# ML
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB

dh_bp = Blueprint('dh_advanced', __name__)

# ===============================
# 🧬 REAL CLUSTERING (KMeans)
# ===============================
@dh_bp.route('/api/clustering')
def clustering():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT text_id, embedding_vector
            FROM ghazal_embeddings
            WHERE embedding_vector IS NOT NULL
            LIMIT 300
        """)
        rows = cur.fetchall()

        ids = []
        vectors = []

        for r in rows:
            emb = r[1]

            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except:
                    continue

            if isinstance(emb, list) and len(emb) > 10:
                ids.append(r[0])
                vectors.append(emb)

        if len(vectors) < 10:
            return jsonify({"error": "Not enough data for clustering"})

        X = np.array(vectors)

        kmeans = KMeans(n_clusters=5, random_state=42)
        labels = kmeans.fit_predict(X)

        results = []
        for i in range(len(ids)):
            results.append({
                "id": ids[i],
                "cluster": int(labels[i])
            })

        return jsonify(results)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cur.close()
        conn.close()


# ===============================
# 🖋️ AUTHORSHIP ATTRIBUTION
# ===============================
@dh_bp.route('/api/authorship')
def authorship():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT t.text_urdu, p.name
            FROM texts t
            JOIN poets p ON t.poet_id = p.id
            WHERE t.form='ghazal'
            LIMIT 300
        """)
        rows = cur.fetchall()

        texts = []
        labels = []

        for r in rows:
            text = r[0] or ""
            poet = r[1]

            if len(text) < 50:
                continue

            texts.append(text)
            labels.append(poet)

        if len(texts) < 20:
            return jsonify({"error": "Not enough data"})

        vectorizer = TfidfVectorizer(max_features=1000)
        X = vectorizer.fit_transform(texts)

        model = MultinomialNB()
        model.fit(X, labels)

        # evaluate on same set (baseline)
        preds = model.predict(X)

        accuracy = sum([1 for i in range(len(labels)) if preds[i] == labels[i]]) / len(labels)

        return jsonify({
            "accuracy": round(accuracy, 3),
            "samples": len(labels),
            "note": "Baseline model (no train/test split yet)"
        })

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cur.close()
        conn.close()


# ===============================
# 📐 METER DETECTION (ARUZ BASIC)
# ===============================
@dh_bp.route('/api/meter')
def meter_detection():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT misra1_urdu
            FROM verses
            WHERE misra1_urdu IS NOT NULL
            LIMIT 200
        """)
        rows = cur.fetchall()

        patterns = []

        for r in rows:
            line = r[0]

            # very basic syllable estimation
            syllables = len(line.split())

            if syllables < 5:
                continue

            patterns.append(syllables)

        counter = Counter(patterns)

        return jsonify({
            "meter_patterns": counter.most_common(5),
            "note": "Approximate syllable-based meter (prototype)"
        })

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cur.close()
        conn.close()


# ===============================
# 🔗 POET INFLUENCE GRAPH
# ===============================
@dh_bp.route('/api/influence')
def influence():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT t.poet_id, g.embedding_vector
            FROM texts t
            JOIN ghazal_embeddings g ON t.id = g.text_id
            WHERE t.form='ghazal'
            LIMIT 300
        """)
        rows = cur.fetchall()

        poet_vectors = defaultdict(list)

        for r in rows:
            poet = r[0]
            emb = r[1]

            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except:
                    continue

            if isinstance(emb, list):
                poet_vectors[poet].append(emb)

        # average vectors
        poet_avg = {}
        for poet, vecs in poet_vectors.items():
            poet_avg[poet] = np.mean(vecs, axis=0)

        # cosine similarity
        edges = []

        poets = list(poet_avg.keys())

        for i in range(len(poets)):
            for j in range(i+1, len(poets)):
                v1 = poet_avg[poets[i]]
                v2 = poet_avg[poets[j]]

                sim = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

                if sim > 0.7:
                    edges.append({
                        "source": poets[i],
                        "target": poets[j],
                        "weight": float(sim)
                    })

        return jsonify(edges)

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cur.close()
        conn.close()