from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os, json, tempfile, re, hashlib
from models.ghazal_model import get_stats, get_all_poets, get_db
from models.bulk_model import (
    is_duplicate, get_or_create_contributor,
    insert_ghazal_bulk, get_books_by_poet,
    analyze_ghazal
)
from modules.embeddings import update_ghazal_embedding   # 🔥 NEW: embedding generation

bulk_bp = Blueprint('bulk', __name__, url_prefix='/bulk')

# ================= HELPER FUNCTIONS =================
def normalize_urdu(text):
    text = text.strip()
    text = text.replace("  ", " ")
    text = text.replace("،", "")
    text = text.replace("۔", "")
    text = text.replace("\n", " ")
    return text.lower()

def hash_text(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def get_first_couplet(text):
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    if len(lines) >= 2:
        return lines[0] + " " + lines[1]
    elif lines:
        return lines[0]
    return ""

def cleanup_temp_file(filepath):
    if filepath and os.path.exists(filepath):
        try:
            os.unlink(filepath)
        except:
            pass

def parse_blocks(text):
    text = text.replace('\r\n', '\n')
    return [b.strip() for b in text.split('###GHZ###') if b.strip()]

# ================= MAIN PAGE =================
@bulk_bp.route('/', methods=['GET'])
def bulk_upload():
    stats = get_stats()
    poets = get_all_poets()

    preview_data = []
    temp_file = session.get('preview_file')
    if temp_file and os.path.exists(temp_file):
        with open(temp_file, 'r', encoding='utf-8') as f:
            preview_data = json.load(f)

    return render_template(
        'bulk.html',
        poets=poets,
        preview_data=preview_data,
        selected_poet_id=session.get('bulk_poet_id', ''),
        selected_book_id=session.get('bulk_book_id', ''),
        contributor_name=session.get('bulk_contributor', ''),
        contributor_email=session.get('bulk_contributor_email', ''),
        stats=stats,
        new_count=session.get('new_ghazals_count', 0)
    )

# ================= PROCESS (PREVIEW) =================
@bulk_bp.route('/process', methods=['POST'])
def bulk_process():
    try:
        poet_id = request.form.get('poet_id')
        if not poet_id:
            flash('Select poet', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        session['bulk_poet_id'] = poet_id
        session['bulk_book_id'] = request.form.get('book_id') or ''
        session['bulk_contributor'] = request.form.get('contributor', '')
        session['bulk_contributor_email'] = request.form.get('contributor_email', '')

        raw_text = ''
        if 'files' in request.files:
            for f in request.files.getlist('files'):
                if f:
                    raw_text += f.read().decode('utf-8', errors='ignore') + "\n"
        pasted = request.form.get('pasted_text')
        if pasted:
            raw_text += pasted

        if not raw_text.strip():
            flash('No data found', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        blocks = parse_blocks(raw_text)
        conn = get_db()
        preview = []
        new_count = 0

        for block in blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if len(lines) < 2:
                continue

            m1 = lines[0]
            m2 = lines[1] if len(lines) > 1 else ''
            verses_count = len(lines) // 2

            normalized = normalize_urdu(block)
            content_hash = hash_text(normalized)
            first_couplet = get_first_couplet(block)
            first_hash = hash_text(normalize_urdu(first_couplet))

            cur = conn.cursor()
            cur.execute("""
                SELECT id, title_urdu FROM texts
                WHERE content_hash = %s OR first_couplet_hash = %s
            """, (content_hash, first_hash))
            row = cur.fetchone()
            cur.close()

            is_dup = row is not None
            existing_id = row['id'] if row else None
            dup_title = row['title_urdu'] if row else None

            preview.append({
                'full_text': block,
                'misra1_urdu': m1,
                'misra2_urdu': m2,
                'verses': verses_count,
                'is_duplicate': is_dup,
                'existing_id': existing_id,
                'content_hash': content_hash,
                'first_couplet_hash': first_hash,
                'normalized_text': normalized
            })
            if not is_dup:
                new_count += 1

        conn.close()

        temp = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        with open(temp.name, 'w', encoding='utf-8') as f:
            json.dump(preview, f, ensure_ascii=False)

        old_file = session.get('preview_file')
        if old_file and os.path.exists(old_file):
            cleanup_temp_file(old_file)

        session['preview_file'] = temp.name
        session['new_ghazals_count'] = new_count

        flash(f'Processed {len(preview)} ghazals. {new_count} new, {len(preview)-new_count} duplicates.', 'success')
        return redirect(url_for('bulk.bulk_upload'))

    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('bulk.bulk_upload'))

# ================= INSERT =================
@bulk_bp.route('/insert', methods=['POST'])
def bulk_insert():
    try:
        temp_file = session.get('preview_file')
        poet_id = session.get('bulk_poet_id')
        book_id = session.get('bulk_book_id') or None
        contributor_name = session.get('bulk_contributor')
        contributor_email = session.get('bulk_contributor_email')

        if not temp_file or not os.path.exists(temp_file):
            flash('Preview expired', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        conn = get_db()
        contributor_id = None
        if contributor_name:
            contributor_id = get_or_create_contributor(conn, contributor_name, contributor_email)

        inserted = 0
        for item in data:
            if item['is_duplicate']:
                continue

            text_id, error = insert_ghazal_bulk(
                conn,
                poet_id=int(poet_id),
                book_id=int(book_id) if book_id else None,
                contributor_id=contributor_id,
                ghazal_text=item['full_text'],
                title_urdu=item['misra1_urdu'],
                content_hash=item['content_hash'],
                first_couplet_hash=item['first_couplet_hash'],
                normalized_text=item['normalized_text']
            )
            if text_id:
                inserted += 1
                # 🔥 NLP analysis (radif, qaafiya, meter, etc.)
                analyze_ghazal(conn, text_id)
                # 🔥 Generate embedding for semantic similarity
                update_ghazal_embedding(text_id)
            else:
                print(f"Insert error: {error}")

        conn.close()
        cleanup_temp_file(temp_file)
        session.clear()

        flash(f'✅ All {inserted} ghazal(s) have been successfully processed and added to the poet\'s list.', 'success')
        return redirect(url_for('main.index'))

    except Exception as e:
        flash(str(e), 'error')
        return redirect(url_for('bulk.bulk_upload'))

# ================= CLEAR =================
@bulk_bp.route('/clear', methods=['POST'])
def bulk_clear():
    temp_file = session.get('preview_file')
    if temp_file:
        cleanup_temp_file(temp_file)
        session.pop('preview_file', None)
    session.pop('bulk_poet_id', None)
    session.pop('bulk_book_id', None)
    session.pop('bulk_contributor', None)
    session.pop('bulk_contributor_email', None)
    session.pop('new_ghazals_count', None)
    flash('Preview cleared', 'info')
    return redirect(url_for('bulk.bulk_upload'))

# ================= BOOKS (AJAX) =================
@bulk_bp.route('/books/<int:poet_id>')
def get_books(poet_id):
    return jsonify({'books': get_books_by_poet(poet_id)})