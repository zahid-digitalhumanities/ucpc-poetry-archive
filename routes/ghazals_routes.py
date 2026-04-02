import hashlib
import os
import time
import traceback
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from markupsafe import Markup
from models.ghazal_model import (
    get_stats, get_all_poets, get_books_by_poet, check_duplicate_ghazal,
    get_or_create_contributor, insert_ghazal, insert_verse,
    get_ghazal_with_verses, get_navigation
)
from modules.analysis import split_verses
from modules.ai_tools import translate_urdu_to_english
from modules.image_generator import generate_ghazal_card

ghazals_bp = Blueprint('ghazals', __name__, url_prefix='/ghazals')

def clean_translation(text: str) -> str:
    if not text:
        return ""
    text = text.strip()
    text = text.replace(" is of", "")
    text = text.replace(" of is", "")
    text = text.replace("  ", " ")
    if len(text) > 1:
        text = text[0].upper() + text[1:]
    return text

@ghazals_bp.route('/add', methods=['GET', 'POST'])
def add_ghazal():
    # (keep your existing implementation)
    pass

@ghazals_bp.route('/books/<int:poet_id>')
def get_books(poet_id):
    books = get_books_by_poet(poet_id)
    return jsonify({'books': books})

@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    stats = get_stats()
    ghazal, verses = get_ghazal_with_verses(text_id)
    if not ghazal:
        flash('Ghazal not found', 'error')
        return redirect(url_for('main.index'))
    mode = session.get('view_mode', 'bilingual')
    prev_id, next_id, total = get_navigation(text_id, ghazal['poet_id'])
    return render_template('view.html',
                           ghazal=ghazal,
                           verses=verses,
                           prev_id=prev_id,
                           next_id=next_id,
                           total_in_poet=total,
                           stats=stats,
                           mode=mode)

@ghazals_bp.route('/set_mode/<mode>')
def set_mode(mode):
    if mode in ['bilingual', 'urdu', 'english']:
        session['view_mode'] = mode
    return redirect(request.referrer or url_for('main.index'))

@ghazals_bp.route('/share_image/<int:text_id>')
def share_image(text_id):
    try:
        dedicator = request.args.get('dedicator', '').strip()
        dedicatee = request.args.get('dedicatee', '').strip()

        ghazal, verses = get_ghazal_with_verses(text_id)
        if not ghazal:
            return jsonify({"error": "Ghazal not found"}), 404

        # Generate image
        img = generate_ghazal_card(ghazal, verses, dedicator, dedicatee)

        # Absolute path from current working directory (works on Render)
        generated_dir = os.path.join(os.getcwd(), 'static', 'generated')
        os.makedirs(generated_dir, exist_ok=True)

        filename = f"{text_id}_{int(time.time())}.png"
        filepath = os.path.join(generated_dir, filename)

        # Save image
        img.save(filepath, 'PNG')
        file_size = os.path.getsize(filepath)
        print(f"✅ Image saved: {filepath} (size: {file_size} bytes)")

        if file_size == 0:
            return jsonify({"error": "Image generation failed (zero size)"}), 500

        base_url = request.host_url.rstrip('/')
        share_url = f"{base_url}/share/{filename}"
        return jsonify({"share_url": share_url})

    except Exception as e:
        print("❌ Error in share_image:")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500