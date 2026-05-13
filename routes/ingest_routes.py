# routes/ingest_routes.py
import os
import json
import tempfile
import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.ingest_pipeline import insert_ghazal, normalize_ghazal
from models.ghazal_model import get_all_poets, get_books_by_poet
from models.base import get_db_connection

ingest_bp = Blueprint('ingest', __name__, url_prefix='/ingest')


# ================= CONTRIBUTOR HELPER =================
def get_or_create_contributor(name, email=None):
    if not name:
        return None
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM contributors WHERE name = %s", (name,))
    row = cur.fetchone()
    if row:
        contributor_id = row['id']
    else:
        cur.execute(
            "INSERT INTO contributors (name, email) VALUES (%s, %s) RETURNING id",
            (name, email)
        )
        contributor_id = cur.fetchone()['id']
        conn.commit()
    cur.close()
    conn.close()
    return contributor_id


# ================= HELPER FUNCTIONS =================
def split_bulk_blocks(text):
    return [b.strip() for b in text.split('###GHZ###') if b.strip()]

def validate_block(block):
    lines = [l.strip() for l in block.split('\n') if l.strip()]
    if len(lines) < 2 or len(lines) % 2 != 0:
        return None, None, 0, False
    return lines[0], lines[1], len(lines)//2, True


# ================= BOOKS (AJAX) =================
@ingest_bp.route('/books/<int:poet_id>')
def get_books(poet_id):
    books = get_books_by_poet(poet_id)
    return jsonify({'books': books})


# ================= SINGLE GHAZAL =================
@ingest_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        poet_id = request.form.get('poet_id', type=int)
        book_id = request.form.get('book_id', type=int) or None
        ghazal_text = request.form.get('ghazal_text', '').strip()
        source = request.form.get('source', '').strip()
        contributor_name = request.form.get('contributor_name', '').strip()
        contributor_email = request.form.get('contributor_email', '').strip()

        if not poet_id or not ghazal_text or not source:
            flash('Poet, text, and source are required.', 'error')
            return redirect(url_for('ingest.add'))

        if "###GHZ###" in ghazal_text:
            flash('Multiple ghazals detected. Please use Bulk Upload tab.', 'error')
            return redirect(url_for('ingest.add'))

        contributor_id = None
        if contributor_name:
            contributor_id = get_or_create_contributor(contributor_name, contributor_email)

        result, error = insert_ghazal(
            poet_id=poet_id,
            ghazal_text=ghazal_text,
            source=source,
            book_id=book_id,
            contributor_id=contributor_id,
            run_nlp_flag=False,   # you can enable later
            run_embedding=False    # you can enable later
        )

        if error:
            flash(error, 'error')
            return redirect(url_for('ingest.add'))

        if result.get('existing'):
            flash(f'⚠️ This ghazal already exists in the archive (existing ID: {result["text_id"]}).', 'warning')
        else:
            flash('✅ Ghazal added successfully!', 'success')
        return redirect(url_for('ghazals.view_ghazal', text_id=result['text_id']))

    poets = get_all_poets()
    return render_template('ghazal_ingest.html', poets=poets)


# ================= BULK PROCESS (PREVIEW) =================
@ingest_bp.route('/bulk-process', methods=['POST'])
def bulk_process():
    try:
        poet_id = request.form.get('poet_id', type=int)
        source = request.form.get('source', '').strip()
        book_id = request.form.get('book_id', type=int) or None

        if not poet_id or not source:
            flash('Poet and source are required.', 'error')
            return redirect(url_for('ingest.add'))

        raw_text = ''

        # File upload
        if 'files' in request.files:
            for f in request.files.getlist('files'):
                if f and f.filename.endswith('.txt'):
                    raw_text += f.read().decode('utf-8', errors='ignore') + "\n"

        pasted = request.form.get('pasted_text', '')
        if pasted:
            raw_text += pasted

        if not raw_text.strip():
            flash('No content provided.', 'error')
            return redirect(url_for('ingest.add'))

        blocks = split_bulk_blocks(raw_text)

        preview = []
        valid_count = 0
        duplicate_count = 0

        conn = get_db_connection()
        cur = conn.cursor()

        for block in blocks:
            m1, m2, verses, valid = validate_block(block)

            if not valid:
                preview.append({
                    'text': block,
                    'error': 'Invalid format (lines must be even)',
                    'is_duplicate': False
                })
                continue

            # Use same normalisation as insert pipeline
            normalized_full = normalize_ghazal(block)
            content_hash = hashlib.sha256(normalized_full.encode('utf-8')).hexdigest()

            cur.execute("SELECT id FROM texts WHERE content_hash = %s", (content_hash,))
            is_dup = cur.fetchone() is not None

            if is_dup:
                duplicate_count += 1
            else:
                valid_count += 1

            preview.append({
                'text': block,
                'misra1': m1,
                'misra2': m2,
                'verses': verses,
                'is_duplicate': is_dup
            })

        cur.close()
        conn.close()

        # Save preview to temp file
        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        with open(temp.name, 'w', encoding='utf-8') as f:
            json.dump(preview, f, ensure_ascii=False)

        session['preview_file'] = temp.name
        session['bulk_poet_id'] = poet_id
        session['bulk_source'] = source
        session['bulk_book_id'] = book_id

        flash(f"""
        📊 Total: {len(blocks)} |
        ✅ Valid: {valid_count} |
        ⚠️ Duplicates: {duplicate_count}
        """, 'success')

        poets = get_all_poets()
        return render_template(
            'ghazal_ingest.html',
            poets=poets,
            preview_data=preview
        )

    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('ingest.add'))


# ================= BULK INSERT =================
@ingest_bp.route('/bulk-insert', methods=['POST'])
def bulk_insert():
    try:
        temp_file = session.get('preview_file')
        poet_id = session.get('bulk_poet_id')
        source = session.get('bulk_source')
        book_id = session.get('bulk_book_id')

        if not temp_file or not os.path.exists(temp_file):
            flash('No preview data found.', 'error')
            return redirect(url_for('ingest.add'))

        with open(temp_file, 'r', encoding='utf-8') as f:
            preview = json.load(f)

        inserted = 0
        skipped = 0
        failed = 0

        for item in preview:
            if item.get('is_duplicate'):
                skipped += 1
                continue

            # Skip invalid blocks
            if item.get('error'):
                failed += 1
                continue

            try:
                result, error = insert_ghazal(
                    poet_id=poet_id,
                    ghazal_text=item['text'],
                    source=source,
                    book_id=book_id,
                    contributor_id=None,
                    run_nlp_flag=False,
                    run_embedding=False
                )
                if error:
                    print(f"Insert error: {error}")
                    failed += 1
                elif result.get('existing'):
                    skipped += 1
                else:
                    inserted += 1
            except Exception as e:
                print(f"Bulk insert error: {e}")
                failed += 1

        # Cleanup
        os.unlink(temp_file)
        session.pop('preview_file', None)
        session.pop('bulk_poet_id', None)
        session.pop('bulk_source', None)
        session.pop('bulk_book_id', None)

        flash(f"""
        ✅ Inserted: {inserted}
        ⚠️ Skipped (duplicates): {skipped}
        ❌ Failed: {failed}
        """, 'success')
        return redirect(url_for('ingest.add'))

    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('ingest.add'))


# ================= BULK CLEAR =================
@ingest_bp.route('/bulk-clear', methods=['POST'])
def bulk_clear():
    temp_file = session.get('preview_file')
    if temp_file and os.path.exists(temp_file):
        os.unlink(temp_file)
    session.pop('preview_file', None)
    session.pop('bulk_poet_id', None)
    session.pop('bulk_source', None)
    session.pop('bulk_book_id', None)
    flash('Preview cleared.', 'info')
    return redirect(url_for('ingest.add'))