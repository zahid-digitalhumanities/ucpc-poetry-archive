from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from models.poets_model import fetch_poet_by_id, get_texts_with_first_verses_paginated
from models.ghazal_model import get_stats
from models.base import get_db_connection
import re

poets_bp = Blueprint('poets', __name__)

def slugify(text):
    """Generate a slug from text (lowercase, spaces to hyphens, remove special chars)."""
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text

@poets_bp.route('/poets')
def poets_list():
    from models.poets_model import fetch_all_poets
    poets = fetch_all_poets()
    stats = get_stats()
    return render_template('poets.html', poets=poets, stats=stats)

@poets_bp.route('/poet/<int:poet_id>')
def poet_detail(poet_id):
    page = request.args.get('page', 1, type=int)
    per_page = 12

    poet = fetch_poet_by_id(poet_id)
    if not poet:
        flash('Poet not found', 'error')
        return redirect(url_for('main.index'))

    texts, total = get_texts_with_first_verses_paginated(poet_id, page, per_page)

    total_pages = (total + per_page - 1) // per_page
    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    return render_template('poet_detail.html',
                           poet=poet,
                           texts=texts,
                           page=page,
                           total_pages=total_pages,
                           prev_page=prev_page,
                           next_page=next_page,
                           total=total)

# ==================== ADD NEW POET (AJAX) ====================
@poets_bp.route('/add_poet', methods=['POST'])
def add_poet():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    name = data.get('name')
    name_urdu = data.get('name_urdu')
    bio_english = data.get('bio_english', '')
    birth_year = data.get('birth_year')
    death_year = data.get('death_year')

    if not name:
        return jsonify({'error': 'Poet name (English) is required'}), 400

    # Generate slug from English name
    slug = slugify(name)

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO poets (name, name_urdu, slug, bio_english, birth_year, death_year)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name, name_urdu, slug, bio_english, birth_year, death_year))
        new_id = cur.fetchone()['id']
        conn.commit()
        return jsonify({'id': new_id, 'name': name, 'name_urdu': name_urdu})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()

# ==================== ADD NEW BOOK (AJAX) ====================
@poets_bp.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid data'}), 400

    poet_id = data.get('poet_id')
    name = data.get('name')
    name_urdu = data.get('name_urdu')

    if not poet_id or not name:
        return jsonify({'error': 'Poet ID and book name are required'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO books (poet_id, name, name_urdu)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (poet_id, name, name_urdu))
        new_id = cur.fetchone()['id']
        conn.commit()
        return jsonify({'id': new_id, 'name': name, 'name_urdu': name_urdu})
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cur.close()
        conn.close()