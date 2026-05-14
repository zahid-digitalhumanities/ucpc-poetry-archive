"""
UCPC Semantic Routes - TEMPORARY MINIMAL VERSION
"""

from flask import Blueprint, request, jsonify, render_template
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

semantic_bp = Blueprint("semantic", __name__, url_prefix="/semantic")


@semantic_bp.route("/")
def semantic_home():
    return render_template("semantic_search.html")


@semantic_bp.route("/api/search", methods=["POST"])
def semantic_search_api():
    return jsonify({
        "success": False,
        "error": "Semantic search is temporarily disabled. Please try again later."
    }), 503


@semantic_bp.route("/api/matla-search", methods=["POST"])
def matla_search_api():
    return jsonify({
        "success": False,
        "error": "Matla search is temporarily disabled. Please try again later."
    }), 503


@semantic_bp.route("/api/intertextual", methods=["POST"])
def intertextual_api():
    return jsonify({
        "success": False,
        "error": "Intertextual analysis is temporarily disabled. Please try again later."
    }), 503


@semantic_bp.route("/api/influence", methods=["POST"])
def influence_search_api():
    return jsonify({
        "success": False,
        "error": "Influence search is temporarily disabled. Please try again later."
    }), 503


@semantic_bp.route("/api/similar/<int:text_id>")
def similar_ghazals_api(text_id):
    return jsonify({
        "success": False,
        "error": "Similar ghazals search is temporarily disabled. Please try again later."
    }), 503


@semantic_bp.route("/api/stats")
def semantic_stats():
    return jsonify({
        "success": True,
        "engine": "UCPC Hybrid Semantic Engine (Disabled)",
        "documents_indexed": 0,
        "retrieval_model": "Coming soon",
        "supports": []
    })
