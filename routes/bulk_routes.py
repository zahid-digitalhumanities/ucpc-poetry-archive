from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os
import json
import tempfile
import re
import uuid
import hashlib
from models.ghazal_model import get_stats, get_all_poets, get_db
from bulk_model import (
    is_duplicate, get_or_create_contributor,
    insert_ghazal_bulk, get_books_by_poet
)

bulk_bp = Blueprint('bulk', __name__, url_prefix='/bulk')

def cleanup_temp_file(filepath):
    if filepath and os.path.exists(filepath):
        try:
            os.unlink(filepath)
        except:
            pass

def parse_blocks(text):
    text = text.replace('\r\n', '\n')
    if '###GHZ###' in text:
        return [b.strip() for b in text.split('###GHZ###') if b.strip()]
    else:
        return [b.strip() for b in re.split(r'\n\s*\n+', text) if b.strip()]

@bulk_bp.route('/')
def bulk_upload():
    stats = get_stats()
    poets = get_all_poets()
    preview_data = session.get('preview_data', [])
    duplicates_found = session.get('duplicates_found', [])
    insert_results = session.get('insert_results', [])

    if not preview_data:
        temp_file = session.get('temp_preview_file')
        if temp_file:
            cleanup_temp_file(temp_file)
            session.pop('temp_preview_file', None)

    return render_template(
        'bulk.html',
        poets=poets,
        preview_data=preview_data,
        duplicates_found=duplicates_found,
        stats=stats,
        insert_results=insert_results
    )

@bulk_bp.route('/preview', methods=['POST'])
def bulk_preview():
    try:
        poet_id = request.form.get('poet_id')
        book_id = request.form.get('book_id') or None
        contributor = request.form.get('contributor', '').strip()
        contributor_email = request.form.get('contributor_email', '').strip()

        if not poet_id:
            flash('❌ Please select a poet', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        session['bulk_poet_id'] = poet_id
        session['bulk_book_id'] = book_id
        session['bulk_contributor'] = contributor
        session['bulk_contributor_email'] = contributor_email

        old_temp = session.get('temp_preview_file')
        if old_temp:
            cleanup_temp_file(old_temp)
            session.pop('temp_preview_file', None)

        raw_blocks = []
        pasted_text = request.form.get('pasted_text', '')
        if pasted_text:
            raw_blocks.extend(parse_blocks(pasted_text))
        elif 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename).lower()
                    file_bytes = file.read()
                    try:
                        text = file_bytes.decode('utf-8')
                    except:
                        try:
                            text = file_bytes.decode('utf-8-sig')
                        except:
                            text = ''
                    if text:
                        raw_blocks.extend(parse_blocks(text))

        if not raw_blocks:
            flash('❌ No valid ghazals found. Check file format (separate with blank lines or ###GHZ###)', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        conn = get_db()
        valid_blocks = []
        malformed_count = 0
        for block in raw_blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            if len(lines) < 2:
                malformed_count += 1
                continue
            valid_blocks.append(block)

        if malformed_count > 0:
            flash(f'⚠️ {malformed_count} ghazal(s) had fewer than 2 lines and were skipped.', 'warning')

        if not valid_blocks:
            flash('❌ No valid ghazals with at least 2 lines found.', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        preview_list = []
        duplicates_list = []
        new_ghazals = []

        for block in valid_blocks:
            lines = [l.strip() for l in block.split('\n') if l.strip()]
            title_urdu = lines[0]
            verses = len(lines) // 2
            is_dup, existing_id, dup_title, dup_poet_id = is_duplicate(conn, block)
            if is_dup:
                cur = conn.cursor()
                cur.execute("SELECT name_urdu FROM poets WHERE id = %s", (dup_poet_id,))
                poet_name = cur.fetchone()['name_urdu'] if cur.rowcount else "Unknown"
                cur.close()
                duplicates_list.append({
                    'title': dup_title,
                    'existing_id': existing_id,
                    'poet_name': poet_name
                })
                preview_list.append({
                    'title_urdu': title_urdu,
                    'verses': verses,
                    'is_duplicate': True,
                    'existing_id': existing_id
                })
            else:
                preview_list.append({
                    'title_urdu': title_urdu,
                    'verses': verses,
                    'is_duplicate': False,
                    'existing_id': None
                })
                new_ghazals.append((block, title_urdu, verses))

        conn.close()

        session['preview_data'] = preview_list
        session['duplicates_found'] = duplicates_list
        session['valid_ghazals_count'] = len(new_ghazals)

        if new_ghazals:
            temp_file = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json')
            temp_file_path = temp_file.name
            data = [{'text': block, 'title': title, 'verses': verses} for block, title, verses in new_ghazals]
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            session['temp_preview_file'] = temp_file_path
        else:
            session['temp_preview_file'] = None

        if duplicates_list:
            flash(f'⚠️ {len(duplicates_list)} duplicate ghazal(s) detected. They will be skipped during insertion.', 'warning')
        if new_ghazals:
            flash(f'✅ Found {len(new_ghazals)} new ghazals ready for upload', 'success')
        else:
            flash('ℹ️ No new ghazals to insert. All are duplicates.', 'info')

        return redirect(url_for('bulk.bulk_upload'))

    except Exception as e:
        flash(f'❌ Error: {str(e)}', 'error')
        return redirect(url_for('bulk.bulk_upload'))

@bulk_bp.route('/insert', methods=['POST'])
def bulk_insert():
    try:
        poet_id = session.get('bulk_poet_id')
        book_id = session.get('bulk_book_id')
        contributor_name = session.get('bulk_contributor')
        contributor_email = session.get('bulk_contributor_email')
        temp_file_path = session.get('temp_preview_file')

        if not temp_file_path or not poet_id:
            flash('❌ No valid ghazals to insert or session expired. Please preview again.', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        if not os.path.exists(temp_file_path):
            flash('❌ Temporary file missing. Please preview again.', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        with open(temp_file_path, 'r', encoding='utf-8') as f:
            new_ghazals = json.load(f)

        if not new_ghazals:
            flash('❌ No valid ghazals to insert', 'error')
            return redirect(url_for('bulk.bulk_upload'))

        conn = get_db()
        contributor_id = None
        if contributor_name:
            contributor_id = get_or_create_contributor(conn, contributor_name, contributor_email)

        results = []
        for ghazal_data in new_ghazals:
            ghazal_text = ghazal_data['text']
            is_dup, existing_id, dup_title, dup_poet_id = is_duplicate(conn, ghazal_text)
            if is_dup:
                results.append({
                    'status': 'duplicate',
                    'title_urdu': ghazal_data['title'],
                    'title_english': '',
                    'verse_count': ghazal_data['verses'],
                    'text_id': None,
                    'existing_id': existing_id
                })
                continue

            text_id, error = insert_ghazal_bulk(
                conn,
                poet_id=int(poet_id),
                book_id=int(book_id) if book_id else None,
                contributor_id=contributor_id,
                ghazal_text=ghazal_text,
                title_urdu=ghazal_data['title']
            )
            if text_id:
                cur = conn.cursor()
                cur.execute("SELECT title_urdu, title_english, verse_count FROM texts WHERE id = %s", (text_id,))
                row = cur.fetchone()
                cur.close()
                results.append({
                    'status': 'inserted',
                    'title_urdu': row['title_urdu'],
                    'title_english': row['title_english'],
                    'verse_count': row['verse_count'],
                    'text_id': text_id,
                    'existing_id': None
                })
            else:
                results.append({
                    'status': 'error',
                    'title_urdu': ghazal_data['title'],
                    'title_english': '',
                    'verse_count': ghazal_data['verses'],
                    'text_id': None,
                    'existing_id': None,
                    'error': error
                })

        conn.commit()
        conn.close()

        cleanup_temp_file(temp_file_path)

        session['insert_results'] = results
        session.pop('preview_data', None)
        session.pop('duplicates_found', None)
        session.pop('valid_ghazals_count', None)
        session.pop('temp_preview_file', None)
        session.pop('bulk_poet_id', None)
        session.pop('bulk_book_id', None)
        session.pop('bulk_contributor', None)
        session.pop('bulk_contributor_email', None)

        flash(f'✅ Inserted {sum(1 for r in results if r["status"] == "inserted")} new ghazals. {sum(1 for r in results if r["status"] == "duplicate")} duplicates skipped.', 'success')
        return redirect(url_for('bulk.bulk_upload'))

    except Exception as e:
        flash(f'❌ Insert failed: {str(e)}', 'error')
        return redirect(url_for('bulk.bulk_upload'))

@bulk_bp.route('/clear', methods=['POST'])
def bulk_clear():
    temp_file = session.pop('temp_preview_file', None)
    if temp_file:
        cleanup_temp_file(temp_file)
    session.pop('preview_data', None)
    session.pop('duplicates_found', None)
    session.pop('valid_ghazals_count', None)
    session.pop('bulk_poet_id', None)
    session.pop('bulk_book_id', None)
    session.pop('bulk_contributor', None)
    session.pop('bulk_contributor_email', None)
    session.pop('insert_results', None)
    flash('Preview cleared. You can start a new bulk upload.', 'info')
    return redirect(url_for('bulk.bulk_upload'))

@bulk_bp.route('/books/<int:poet_id>')
def get_books(poet_id):
    books = get_books_by_poet(poet_id)
    return jsonify({'books': books})
