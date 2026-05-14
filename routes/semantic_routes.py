"""
UCPC Semantic Routes
Research-grade semantic retrieval API for Digital Humanities infrastructure.
"""

from flask import Blueprint, request, jsonify, render_template
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from semantic.semantic_search_v2 import get_semantic_engine, search_semantic
from modules.intertextual_analysis import IntertextualAnalyzer

semantic_bp = Blueprint("semantic", __name__, url_prefix="/semantic")
intertextual = IntertextualAnalyzer()


@semantic_bp.route("/")
def semantic_home():
    return render_template("semantic_search.html")


@semantic_bp.route("/api/search", methods=["POST"])
def semantic_search_api():
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        top_n = int(data.get("top_n", 10))
        if not query:
            return jsonify({"success": False, "error": "No query provided"}), 400
        results = search_semantic(query, top_n=top_n)
        return jsonify({
            "success": True,
            "query": query,
            "method": "Hybrid Semantic Retrieval (Embeddings + BM25 + Intertextuality)",
            "results_count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@semantic_bp.route("/api/matla-search", methods=["POST"])
def matla_search_api():
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"success": False, "error": "No matla query"}), 400
        engine = get_semantic_engine()
        results = engine.search(query, top_n=20)
        matla_results = []
        for r in results:
            matla = r.get("matla") or ""
            if query in matla:
                r["match_type"] = "Exact Matla Match"
                matla_results.append(r)
            else:
                similarity = intertextual.sequence_similarity(query, matla)
                if similarity >= 0.40:
                    r["match_type"] = "Partial Matla Match"
                    matla_results.append(r)
        matla_results = sorted(matla_results, key=lambda x: x["score"], reverse=True)
        return jsonify({
            "success": True,
            "query": query,
            "results_count": len(matla_results),
            "results": matla_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@semantic_bp.route("/api/intertextual", methods=["POST"])
def intertextual_api():
    try:
        data = request.json or {}
        text_a = data.get("text_a", "").strip()
        text_b = data.get("text_b", "").strip()
        if not text_a or not text_b:
            return jsonify({"success": False, "error": "Both texts required"}), 400
        analysis = intertextual.analyze(text_a, text_b)
        return jsonify({
            "success": True,
            "method": "Computational Intertextuality",
            "analysis": analysis
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@semantic_bp.route("/api/influence", methods=["POST"])
def influence_search_api():
    try:
        data = request.json or {}
        query = data.get("query", "").strip()
        threshold = float(data.get("threshold", 0.60))
        if not query:
            return jsonify({"success": False, "error": "No query"}), 400
        engine = get_semantic_engine()
        results = engine.influence_search(query, threshold=threshold)
        return jsonify({
            "success": True,
            "query": query,
            "threshold": threshold,
            "method": "Intertextual Influence Detection",
            "results_count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@semantic_bp.route("/api/similar/<int:text_id>")
def similar_ghazals_api(text_id):
    try:
        engine = get_semantic_engine()
        results = engine.find_similar_by_id(text_id, top_n=10)
        return jsonify({
            "success": True,
            "text_id": text_id,
            "method": "Semantic Similarity Retrieval",
            "results_count": len(results),
            "results": results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@semantic_bp.route("/api/stats")
def semantic_stats():
    try:
        engine = get_semantic_engine()
        total_docs = len(engine.documents)
        return jsonify({
            "success": True,
            "engine": "UCPC Hybrid Semantic Engine",
            "documents_indexed": total_docs,
            "retrieval_model": "SentenceTransformer + BM25",
            "supports": ["semantic retrieval", "matla search", "intertextual analysis", "influence detection", "hybrid ranking"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
