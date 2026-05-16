from flask import Blueprint, render_template, abort
from models.poet_prediction_model import predict_poet
from models.ghazal_model import get_ghazal_with_verses

poet_bp = Blueprint('poet_prediction', __name__, url_prefix='/predict')

@poet_bp.route('/similar/<int:text_id>')
def predict_similar(text_id):
    print(f"🔥 ROUTE HIT for {text_id}")
    try:
        result = get_ghazal_with_verses(text_id)
        if not result or not result[0]:
            abort(404)
        ghazal, _ = result
        predictions = predict_poet(text_id, top_n=3)
        return render_template('predict_poet.html', ghazal=ghazal, predictions=predictions)
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        abort(500)