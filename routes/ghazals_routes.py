import hashlib
import os
import time
from io import BytesIO
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from markupsafe import Markup
from models.ghazal_model import (
    get_stats, get_all_poets, get_books_by_poet, check_duplicate_ghazal,
    get_or_create_contributor, insert_ghazal, insert_verse,
    get_ghazal_with_verses, get_navigation
)
from modules.analysis import split_verses
from modules.ai_tools import translate_urdu_to_english
from modules.image_generator import generate_ghazal_card

# ---------- Blueprint definition first! ----------
ghazals_bp = Blueprint('ghazals', __name__, url_prefix='/ghazals')
# -----------------------------------------------

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
    stats = get_stats()
    poets = get_all_poets()
    books = []
    selected_poet_id = None
    selected_book_id = None
    form_data = {}

    if request.method == 'POST':
        poet_id = request.form.get('poet_id')
        book_id = request.form.get('book_id') or None
        contributor_name = request.form.get('contributor_name', '').strip()
        contributor_email = request.form.get('contributor_email', '').strip()
        ghazal_text = request.form.get('ghazal_text', '').strip()

        form_data = {
            'ghazal_text': ghazal_text,
            'contributor_name': contributor_name,
            'contributor_email': contributor_email,
        }
        selected_poet_id = poet_id
        selected_book_id = book_id

        if not poet_id:
            flash('❌ Please select a poet.', 'error')
            return render_template('add_ghazal.html', stats=stats, poets=poets,
                                   books=books, selected_poet_id=selected_poet_id,
                                   selected_book_id=selected_book_id, form_data=form_data)

        if not ghazal_text:
            flash('❌ Please enter ghazal text.', 'error')
            return render_template('add_ghazal.html', stats=stats, poets=poets,
                                   books=books, selected_poet_id=selected_poet_id,
                                   selected_book_id=selected_book_id, form_data=form_data)

        content_hash = hashlib.sha256(ghazal_text.encode('utf-8')).hexdigest()
        is_dup, existing = check_duplicate_ghazal(content_hash)
        if is_dup:
            flash('⚠️ This ghazal already exists!', 'warning')
            return render_template('add_ghazal.html', stats=stats, poets=poets,
                                   books=books, selected_poet_id=selected_poet_id,
                                   selected_book_id=selected_book_id, form_data=form_data,
                                   duplicate_found=True, existing_ghazal=existing)

        verses = split_verses(ghazal_text)
        if not verses:
            flash('❌ Could not parse verses. Please check format (each couplet on two lines).', 'error')
            return render_template('add_ghazal.html', stats=stats, poets=poets,
                                   books=books, selected_poet_id=selected_poet_id,
                                   selected_book_id=selected_book_id, form_data=form_data)

        title_urdu = verses[0][0] if verses else ghazal_text[:100]
        title_english_raw = translate_urdu_to_english(title_urdu)
        title_english = clean_translation(title_english_raw)

        translated_verses = []
        text_english_parts = []
        for (m1, m2) in verses:
            m1_en_raw = translate_urdu_to_english(m1)
            m2_en_raw = translate_urdu_to_english(m2) if m2 else ''
            m1_en = clean_translation(m1_en_raw)
            m2_en = clean_translation(m2_en_raw) if m2 else ''
            if len(m1_en.split()) <= 2:
                m1_en = "[Translation unavailable]"
            if m2 and len(m2_en.split()) <= 2:
                m2_en = "[Translation unavailable]"
            translated_verses.append((m1_en, m2_en))
            text_english_parts.append(f"{m1_en}\n{m2_en}" if m2_en else m1_en)

        text_english = '\n\n'.join(text_english_parts)

        contributor_id = None
        if contributor_name:
            contributor_id = get_or_create_contributor(contributor_name, contributor_email)

        try:
            text_id = insert_ghazal(
                poet_id=poet_id,
                book_id=book_id,
                contributor_id=contributor_id,
                title_urdu=title_urdu,
                title_english=title_english,
                text_urdu=ghazal_text,
                text_english=text_english,
                content_hash=content_hash,
                verse_count=len(verses)
            )

            for idx, ((m1, m2), (m1_en, m2_en)) in enumerate(zip(verses, translated_verses), 1):
                insert_verse(text_id, idx, m1, m2, m1_en, m2_en)

            flash(f'✨ Thank you {contributor_name or "contributor"}! Your ghazal has been added.', 'success')
            flash(Markup(f'📖 <a href="{url_for("ghazals.view_ghazal", text_id=text_id)}" class="underline">Click here to view your ghazal</a>'), 'success')
            return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

        except Exception as e:
            flash(f'❌ Error saving ghazal: {str(e)}', 'error')
            return render_template('add_ghazal.html', stats=stats, poets=poets,
                                   books=books, selected_poet_id=selected_poet_id,
                                   selected_book_id=selected_book_id, form_data=form_data)

    # GET request
    selected_poet_id = request.args.get('poet_id')
    if selected_poet_id:
        books = get_books_by_poet(selected_poet_id)

    return render_template('add_ghazal.html', stats=stats, poets=poets,
                           books=books, selected_poet_id=selected_poet_id,
                           selected_book_id=None, form_data=None)

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
    """Generate ghazal PNG, save it, and return shareable URL."""
    dedicator = request.args.get('dedicator', '').strip()
    dedicatee = request.args.get('dedicatee', '').strip()

    ghazal, verses = get_ghazal_with_verses(text_id)
    if not ghazal:
        return jsonify({"error": "Ghazal not found"}), 404

    # Generate image
    img = generate_ghazal_card(ghazal, verses, dedicator, dedicatee)

    # Ensure directory exists
    generated_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'generated')
    generated_dir = os.path.abspath(generated_dir)
    os.makedirs(generated_dir, exist_ok=True)

    # Unique filename
    filename = f"{text_id}_{int(time.time())}.png"
    filepath = os.path.join(generated_dir, filename)

    # Save image
    img.save(filepath, 'PNG')

    # Build URLs
    base_url = request.host_url.rstrip('/')
    image_url = f"{base_url}/static/generated/{filename}"
    share_url = f"{base_url}/share/{filename}"

    return jsonify({
        "image_url": image_url,
        "share_url": share_url
    })