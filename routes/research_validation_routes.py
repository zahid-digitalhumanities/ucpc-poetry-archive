"""
Research validation API routes for UCPC.
Provides endpoints for evaluation metrics, confusion analysis, and stylometric reports.
"""

from flask import Blueprint, jsonify, request
import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from modules.evaluation_metrics import EvaluationMetrics
from modules.confusion_analysis import ConfusionAnalyzer
from modules.stylometric_validation import StylometricValidator
from modules.semantic_evaluation import SemanticEvaluator

validation_bp = Blueprint('validation', __name__, url_prefix='/research/validation')


@validation_bp.route('/health')
def health():
    return jsonify({"status": "ok", "module": "Research Validation API"})


@validation_bp.route('/poet-metrics')
def poet_metrics():
    try:
        report_path = os.path.join(BASE_DIR, 'evaluation', 'full_evaluation_report.json')
        if os.path.exists(report_path):
            with open(report_path, 'r', encoding='utf-8') as f:
                report = json.load(f)
            return jsonify({"success": True, "metrics": report})
        else:
            return jsonify({
                "success": False,
                "error": "Run evaluation first: python scripts/run_research_evaluation.py"
            })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@validation_bp.route('/stylometric-profile', methods=['POST'])
def stylometric_profile():
    data = request.json or {}
    text = data.get('text', '')
    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400
    validator = StylometricValidator()
    profile = validator.stylometric_profile(text)
    return jsonify({"success": True, "profile": profile})


@validation_bp.route('/stylometric-compare', methods=['POST'])
def stylometric_compare():
    data = request.json or {}
    text_a = data.get('text_a', '')
    text_b = data.get('text_b', '')
    if not text_a or not text_b:
        return jsonify({"success": False, "error": "Both texts required"}), 400
    validator = StylometricValidator()
    comparison = validator.compare_profiles(text_a, text_b)
    return jsonify({"success": True, "comparison": comparison})


@validation_bp.route('/semantic-evaluate', methods=['POST'])
def semantic_evaluate():
    data = request.json or {}
    evaluations = data.get('evaluations', [])
    if not evaluations:
        return jsonify({"success": False, "error": "No evaluations provided"}), 400
    evaluator = SemanticEvaluator()
    results = evaluator.corpus_evaluation(evaluations, k=5)
    results["interpretation"] = evaluator.interpret_results(results)
    return jsonify({"success": True, "evaluation": results})