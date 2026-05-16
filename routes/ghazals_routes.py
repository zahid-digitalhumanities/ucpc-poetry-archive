from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from models.ghazal_model import (
    get_all_poets, get_books_by_poet,
    insert_ghazal, insert_verse,
    check_duplicate_ghazal, get_poet_by_id,
    get_ghazal_with_verses, get_navigation,
    get_or_create_contributor
)
from models.poets_model import fetch_poet_by_id
from models.bulk_model import analyze_ghazal   # NLP analysis
from models.base import get_db_connection
# from modules.embeddings import update_ghazal_embedding   # 🔥 DISABLED for free tier
import hashlib
import re

ghazals_bp = Blueprint('ghazals', __name__, url_prefix='/ghazals')

@ghazals_bp.route('/add', methods=['GET', 'POST'])
def add_ghazal():
    if request.method == 'POST':
        poet_id = request.form.get('poet_id', type=int)
        book_id = request.form.get('book_id', type=int) or None
        ghazal_text = request.form.get('ghazal_text', '').strip()
        contributor_name = request.form.get('contributor_name', '').strip()
        contributor_email = request.form.get('contributor_email', '').strip()

        if not poet_id or not ghazal_text:
            flash('Poet and Ghazal text are required.', 'error')
            return redirect(url_for('ghazals.add_ghazal'))

        # Compute content hash for duplicate detection
        content_hash = hashlib.sha256(ghazal_text.encode('utf-8')).hexdigest()

        # Check for duplicate
        is_dup, existing = check_duplicate_ghazal(content_hash)
        if is_dup:
            poet = fetch_poet_by_id(existing['poet_id'])
            existing['poet_name'] = poet['name'] if poet else 'Unknown'
            existing['poet_name_urdu'] = poet['name_urdu'] if poet else ''
            return render_template('add_ghazal.html',
                                 poets=get_all_poets(),
                                 duplicate_found=True,
                                 existing_ghazal=existing,
                                 form_data=request.form)

        # Normalize line endings
        ghazal_text = ghazal_text.replace('\r\n', '\n')
        # Split into couplets (separated by blank lines)
        couplets = re.split(r'\n\s*\n', ghazal_text)
        if len(couplets) == 1 and '\n' in ghazal_text:
            lines = ghazal_text.split('\n')
            couplets = []
            for i in range(0, len(lines), 2):
                if i+1 < len(lines):
                    couplets.append(f"{lines[i]}\n{lines[i+1]}")
                else:
                    couplets.append(lines[i])
        verse_count = len(couplets)

        # First line of first couplet becomes Urdu title
        first_couplet = couplets[0].split('\n')
        title_urdu = first_couplet[0][:100] if first_couplet else ''
        title_english = ''  # optional, can be auto‑translated later

        # Get or create contributor (if name provided)
        contributor_id = None
        if contributor_name:
            contributor_id = get_or_create_contributor(contributor_name, contributor_email)

        # Insert ghazal into `texts` table
        text_id = insert_ghazal(
            poet_id=poet_id,
            book_id=book_id,
            contributor_id=contributor_id,
            title_urdu=title_urdu,
            title_english=title_english,
            text_urdu=ghazal_text,
            text_english='',
            content_hash=content_hash,
            verse_count=verse_count
        )

        # Insert each verse into `verses` table
        for idx, couplet in enumerate(couplets, start=1):
            lines = couplet.strip().split('\n')
            misra1 = lines[0] if len(lines) > 0 else ''
            misra2 = lines[1] if len(lines) > 1 else ''
            insert_verse(text_id, idx, misra1, misra2, '', '')

        # 🔥 NLP analysis (radif, qaafiya, meter, etc.)
        conn = get_db_connection()
        analyze_ghazal(conn, text_id)
        conn.close()

        # 🔥 Generate embedding for semantic similarity - DISABLED for free tier
        # update_ghazal_embedding(text_id)  # COMMENTED OUT

        flash('Ghazal added successfully!', 'success')
        return redirect(url_for('ghazals.view_ghazal', text_id=text_id))

    # GET request – show empty form
    poets = get_all_poets()
    return render_template('add_ghazal.html', poets=poets, duplicate_found=False)

@ghazals_bp.route('/books/<int:poet_id>')
def get_books(poet_id):
    """Return JSON list of books for a poet (used by AJAX)."""
    books = get_books_by_poet(poet_id)
    return jsonify({'books': books})

@ghazals_bp.route('/view/<int:text_id>')
def view_ghazal(text_id):
    """Display a ghazal with all its couplets (Urdu only)."""
    result = get_ghazal_with_verses(text_id)
    if not result:
        abort(404)
    if isinstance(result, tuple):
        ghazal, verses = result
    else:
        ghazal = result.get('ghazal')
        verses = result.get('verses')
    if not ghazal:
        abort(404)

    prev_id, next_id, total = get_navigation(text_id, ghazal['poet_id'])
    return render_template('view.html',
                         ghazal=ghazal,
                         verses=verses,
                         prev_id=prev_id,
                         next_id=next_id,
                         total=total)
