# ============================================
# UCPC Semantic Routes
# ============================================

from flask import Blueprint, jsonify, render_template, request
from semantic.semantic_search_v2 import search_semantic

semantic_bp = Blueprint("semantic", __name__, url_prefix="/semantic")

@semantic_bp.route("/")
def semantic_home():
    return render_template("semantic_search.html")

@semantic_bp.route("/api/search", methods=["POST"])
def semantic_api():
    data = request.get_json()
    query = data.get("query", "").strip()
    if not query:
        return jsonify({"success": False, "message": "Empty query"})
    results = search_semantic(query)
    return jsonify({
        "success": True,
        "method": "TF-IDF Semantic Retrieval",
        "results": results
    })
