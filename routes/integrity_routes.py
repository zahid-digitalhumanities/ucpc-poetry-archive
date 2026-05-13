from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request,
    jsonify
)

from models.base import get_db_connection

from models.integrity_model import (
    get_duplicate_stats,
    get_duplicate_groups,
    get_attribution_conflicts,
    get_near_duplicates,
    get_matla_collisions,
    get_canonical_variants
)

integrity_bp = Blueprint(
    'integrity',
    __name__,
    url_prefix='/integrity'
)


# =========================================================
# DASHBOARD
# =========================================================
@integrity_bp.route('/')
def integrity_dashboard():
    return render_template('integrity_dashboard.html')


# =========================================================
# API: STATS
# =========================================================
@integrity_bp.route('/api/stats')
def api_stats():
    try:
        stats = get_duplicate_stats()
        duplicate_groups = get_duplicate_groups(limit=100) or []
        conflicts = get_attribution_conflicts(limit=100) or []
        near_duplicates = get_near_duplicates(limit=50) or []
        matla_collisions = get_matla_collisions(limit=100) or []

        stats['exact_duplicate_count'] = sum(
            (row['copies'] - 1) for row in duplicate_groups
        ) if duplicate_groups else 0

        stats['conflict_count'] = len(conflicts)
        stats['near_duplicate_count'] = len(near_duplicates)
        stats['matla_collision_count'] = sum(
            (row['record_count'] - 1) for row in matla_collisions
        ) if matla_collisions else 0

        stats['clean_records'] = max(0,
            stats['total_ghazals']
            - stats['exact_duplicate_count']
            - stats['conflict_count']
            - stats['near_duplicate_count']
        )

        return jsonify(stats)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =========================================================
# API: DUPLICATE GROUPS
# =========================================================
@integrity_bp.route('/api/duplicate-groups')
def api_duplicate_groups():
    try:
        groups = get_duplicate_groups(limit=100)
        return jsonify(groups or [])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =========================================================
# API: ATTRIBUTION CONFLICTS
# =========================================================
@integrity_bp.route('/api/attribution-conflicts')
def api_attribution_conflicts():
    try:
        conflicts = get_attribution_conflicts(limit=100)
        return jsonify(conflicts or [])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =========================================================
# API: NEAR DUPLICATES
# =========================================================
@integrity_bp.route('/api/near-duplicates')
def api_near_duplicates():
    try:
        near_duplicates = get_near_duplicates(limit=50)
        return jsonify(near_duplicates or [])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =========================================================
# API: MATLA COLLISIONS
# =========================================================
@integrity_bp.route('/api/matla-collisions')
def api_matla_collisions():
    try:
        collisions = get_matla_collisions(limit=100)
        return jsonify(collisions or [])
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# =========================================================
# VARIANTS
# =========================================================
@integrity_bp.route('/variants/<string:hash_value>')
def canonical_variants(hash_value):
    try:
        variants = get_canonical_variants(hash_value)
        return jsonify(variants or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500