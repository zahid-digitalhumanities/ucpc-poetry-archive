from flask import Blueprint, redirect, url_for

# This blueprint handles /poet/<id> and redirects to /poets/<id>
poet_redirect_bp = Blueprint('poet_redirect', __name__, url_prefix='/poet')

@poet_redirect_bp.route('/<int:poet_id>')
def poet_redirect(poet_id):
    return redirect(url_for('poets.poet_detail', poet_id=poet_id), 301)

@poet_redirect_bp.route('/')
def poet_list_redirect():
    return redirect(url_for('poets.poets_list'), 301)
