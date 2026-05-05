# models/ingest_pipeline.py
import uuid
import hashlib
import re
from models.base import get_db_connection

# ================= NORMALIZATION =================
def normalize_ghazal(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('،', '').replace('۔', '').replace('.', '').replace('!', '')
    return text.lower()

def sha256_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()

# ================= SPLIT COUPLETS =================
def split_couplets(text):
    """Return list of (misra1, misra2) pairs."""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    pairs = []
    for i in range(0, len(lines) - 1, 2):
        pairs.append((lines[i], lines[i+1]))
    # If odd number of lines, drop last incomplete line
    return pairs

# ================= NLP (RADIF/QAAFIYA) – LIGHTWEIGHT =================
def run_nlp(text):
    """Minimal NLP to avoid breaking bulk insert."""
    # For now, return empty/placeholder – you can integrate real modules later
    return {
        'radif': None,
        'qaafiya': [],
        'confidence': 0.0,
        'meter_name': None,
        'meter_pattern': None,
        'meter_confidence': 0.0,
        'theme': None
    }

# ================= MAIN INSERT FUNCTION =================
def insert_ghazal(poet_id, ghazal_text, source, book_id=None, contributor_id=None,
                  title_urdu=None, title_english=None, translation_english=None,
                  external_id=None, run_nlp_flag=False, run_embedding=False):
    """
    Insert a ghazal with minimal fields – safe for bulk.
    NLP and embedding are optional (off by default for stability).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # ----- Normalize and compute hashes -----
        normalized_full = normalize_ghazal(ghazal_text)
        content_hash = sha256_hash(normalized_full)

        # Split couplets
        pairs = split_couplets(ghazal_text)
        if not pairs:
            return None, "Invalid ghazal format: no valid couplets"

        # First couplet hash
        first_misra1, first_misra2 = pairs[0]
        first_couplet_normalized = normalize_ghazal(first_misra1 + " " + first_misra2)
        first_couplet_hash = md5_hash(first_couplet_normalized)

        # Title (use first misra if not provided)
        if not title_urdu:
            title_urdu = first_misra1[:100]

        verse_count = len(pairs)
        public_id = str(uuid.uuid4())[:8]

        # ----- Insert into texts (matching your schema) -----
        cur.execute("""
            INSERT INTO texts (
                public_id,
                poet_id,
                book_id,
                contributor_id,

                title,              -- required, same as title_urdu
                title_urdu,
                title_english,

                text_urdu,
                text_english,

                verse_count,
                content_hash,

                form,
                language,

                first_couplet_hash,
                normalized_text,

                source,
                external_id,
                translation_english,

                created_at
            )
            VALUES (%s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    NOW())
            RETURNING id
        """, (
            public_id,
            poet_id,
            book_id,
            contributor_id,

            title_urdu,          # title (same as title_urdu)
            title_urdu,          # title_urdu
            title_english or "",

            ghazal_text,
            "",                  # text_english

            verse_count,
            content_hash,

            'ghazal',
            'ur',

            first_couplet_hash,
            normalized_full,

            source,
            external_id,
            translation_english or ""
        ))
        text_id = cur.fetchone()['id']

        # ----- Insert verses (matching your schema) -----
        for idx, (m1, m2) in enumerate(pairs, 1):
            cur.execute("""
                INSERT INTO verses (
                    text_id,
                    couplet_index,

                    misra1,
                    misra2,

                    misra1_urdu,
                    misra2_urdu,

                    misra1_english,
                    misra2_english,

                    search_text,
                    verse_count
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                text_id,
                idx,

                m1,          # misra1
                m2,          # misra2

                m1,          # misra1_urdu
                m2,          # misra2_urdu

                "", "",      # English placeholder
                f"{m1} {m2}",
                verse_count
            ))

        conn.commit()

        # ----- Optional NLP (off by default) -----
        if run_nlp_flag:
            try:
                nlp_result = run_nlp(ghazal_text)
                # Convert qaafiya to array if it's a string
                qaafiya = nlp_result.get('qaafiya', [])
                if isinstance(qaafiya, str):
                    qaafiya = [qaafiya]
                cur.execute("""
                    INSERT INTO poetic_features (
                        text_id, radif, qaafiya, confidence,
                        meter_name, meter_pattern, meter_confidence, theme
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (text_id) DO UPDATE SET
                        radif = EXCLUDED.radif,
                        qaafiya = EXCLUDED.qaafiya,
                        confidence = EXCLUDED.confidence,
                        meter_name = EXCLUDED.meter_name,
                        meter_pattern = EXCLUDED.meter_pattern,
                        meter_confidence = EXCLUDED.meter_confidence,
                        theme = EXCLUDED.theme
                """, (
                    text_id,
                    nlp_result.get('radif'),
                    qaafiya,
                    nlp_result.get('confidence'),
                    nlp_result.get('meter_name'),
                    nlp_result.get('meter_pattern'),
                    nlp_result.get('meter_confidence'),
                    nlp_result.get('theme')
                ))
                conn.commit()
            except Exception as e:
                print(f"NLP error for text_id {text_id}: {e}")

        # ----- Embedding (disabled for now) -----
        if run_embedding:
            try:
                # Import inside function to avoid circular imports
                from modules.embeddings import update_ghazal_embedding
                update_ghazal_embedding(text_id)
            except Exception as e:
                print(f"Embedding error for text_id {text_id}: {e}")

        print(f"✅ Inserted ghazal ID: {text_id}")
        return {"text_id": text_id, "prediction": None}, None

    except Exception as e:
        conn.rollback()
        err_msg = str(e)
        print(f"❌ Insert error: {err_msg}")
        return None, err_msg

    finally:
        cur.close()
        conn.close()