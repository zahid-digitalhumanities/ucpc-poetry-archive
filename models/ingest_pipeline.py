# models/ingest_pipeline.py
import uuid
import hashlib
import re
import logging
from contextlib import contextmanager
from models.base import get_db_connection

# Configure logging for supervisor visibility
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= NORMALIZATION =================
def normalize_ghazal(text):
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    # Remove common diacritics/punctuation but keep Urdu letters
    text = re.sub(r'[،۔.!؟]', '', text)
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
    return pairs

# ================= NLP (PLACEHOLDER) =================
def run_nlp(text):
    """Minimal NLP – replace with actual module later."""
    return {
        'radif': None,
        'qaafiya': [],
        'confidence': 0.0,
        'meter_name': None,
        'meter_pattern': None,
        'meter_confidence': 0.0,
        'theme': None
    }

# ================= DUPLICATE CHECK =================
def _ghazal_exists(cur, content_hash):
    """Return (exists, text_id) if ghazal with this hash already exists."""
    cur.execute(
        "SELECT id FROM texts WHERE content_hash = %s LIMIT 1",
        (content_hash,)
    )
    row = cur.fetchone()
    return (True, row['id']) if row else (False, None)

def _poet_exists(cur, poet_id):
    """Validate poet_id exists in database."""
    cur.execute("SELECT id FROM poets WHERE id = %s", (poet_id,))
    return cur.fetchone() is not None

# ================= MAIN INSERT (GOLD GRADE) =================
def insert_ghazal(poet_id, ghazal_text, source, book_id=None, contributor_id=None,
                  title_urdu=None, title_english=None, translation_english=None,
                  external_id=None, run_nlp_flag=False, run_embedding=False):
    """
    Insert a ghazal with full duplicate protection and validation.
    
    Returns:
        (result_dict, error_message) where result_dict contains 'text_id' (new or existing)
        and optional 'existing' flag.
    """
    # ----- Basic input validation -----
    if not ghazal_text or len(ghazal_text.strip()) < 20:
        return None, "Ghazal text too short (minimum 20 characters)"
    
    if len(ghazal_text) > 50000:  # safety limit
        return None, "Ghazal text exceeds 50KB limit"
    
    # Use context manager for connection & cursor (auto-rollback on exception)
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Validate poet exists
            if not _poet_exists(cur, poet_id):
                return None, f"Poet with id {poet_id} does not exist"
            
            # 2. Normalize and hash full ghazal
            normalized_full = normalize_ghazal(ghazal_text)
            content_hash = sha256_hash(normalized_full)
            
            # 3. Check for existing duplicate (global, across all poets)
            exists, existing_id = _ghazal_exists(cur, content_hash)
            if exists:
                logger.warning(f"Duplicate ghazal detected (content_hash: {content_hash[:16]}...). Returning existing text_id={existing_id}")
                conn.commit()  # no changes, but close cleanly
                return {"text_id": existing_id, "existing": True}, None
            
            # 4. Split couplets & validate
            pairs = split_couplets(ghazal_text)
            if len(pairs) == 0:
                return None, "Invalid ghazal format: no complete couplets found"
            if len(pairs) > 50:  # sanity
                return None, f"Too many couplets ({len(pairs)}), max 50"
            
            # 5. First couplet hash
            first_m1, first_m2 = pairs[0]
            first_couplet_normalized = normalize_ghazal(first_m1 + " " + first_m2)
            first_couplet_hash = md5_hash(first_couplet_normalized)
            
            # 6. Title defaults
            effective_title_urdu = title_urdu or first_m1[:100]
            effective_title_english = title_english or ""
            
            # 7. Prepare metadata
            verse_count = len(pairs)
            public_id = str(uuid.uuid4())[:8]
            
            # 8. Insert into texts
            cur.execute("""
                INSERT INTO texts (
                    public_id, poet_id, book_id, contributor_id,
                    title, title_urdu, title_english,
                    text_urdu, text_english,
                    verse_count, content_hash,
                    form, language,
                    first_couplet_hash, normalized_text,
                    source, external_id, translation_english,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    NOW()
                )
                RETURNING id
            """, (
                public_id, poet_id, book_id, contributor_id,
                effective_title_urdu, effective_title_urdu, effective_title_english,
                ghazal_text, "",
                verse_count, content_hash,
                'ghazal', 'ur',
                first_couplet_hash, normalized_full,
                source, external_id, translation_english or ""
            ))
            text_id = cur.fetchone()['id']
            
            # 9. Insert verses (batch insert is better, but keep simple for safety)
            for idx, (m1, m2) in enumerate(pairs, 1):
                cur.execute("""
                    INSERT INTO verses (
                        text_id, couplet_index,
                        misra1, misra2,
                        misra1_urdu, misra2_urdu,
                        misra1_english, misra2_english,
                        search_text, verse_count
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    text_id, idx,
                    m1, m2,
                    m1, m2,
                    "", "",
                    f"{m1} {m2}",
                    verse_count
                ))
            
            # 10. Commit transaction (all or nothing)
            conn.commit()
            logger.info(f"✅ Inserted NEW ghazal ID: {text_id} (poet_id={poet_id}, couplets={verse_count})")
            
    except Exception as e:
        conn.rollback()
        err_msg = f"Database error: {str(e)}"
        logger.error(f"❌ Insert failed: {err_msg}")
        return None, err_msg
    finally:
        conn.close()
    
    # ----- Optional NLP (outside main transaction to avoid rollback on failure) -----
    if run_nlp_flag:
        try:
            # Reopen connection for optional features (isolated)
            conn2 = get_db_connection()
            with conn2.cursor() as cur2:
                nlp_result = run_nlp(ghazal_text)
                qaafiya = nlp_result.get('qaafiya', [])
                if isinstance(qaafiya, str):
                    qaafiya = [qaafiya]
                cur2.execute("""
                    INSERT INTO poetic_features (
                        text_id, radif, qaafiya, confidence,
                        meter_name, meter_pattern, meter_confidence, theme
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (text_id) DO UPDATE SET
                        radif = EXCLUDED.radif,
                        qaafiya = EXCLUDED.qaafiya,
                        confidence = EXCLUDED.confidence,
                        meter_name = EXCLUDED.meter_name,
                        meter_pattern = EXCLUDED.meter_pattern,
                        meter_confidence = EXCLUDED.meter_confidence,
                        theme = EXCLUDED.theme
                """, (
                    text_id, nlp_result.get('radif'), qaafiya, nlp_result.get('confidence'),
                    nlp_result.get('meter_name'), nlp_result.get('meter_pattern'),
                    nlp_result.get('meter_confidence'), nlp_result.get('theme')
                ))
                conn2.commit()
                logger.info(f"✅ NLP features added for text_id {text_id}")
        except Exception as e:
            logger.warning(f"NLP failed for text_id {text_id}: {e}")
        finally:
            conn2.close()
    
    # ----- Embedding (optional) -----
    if run_embedding:
        try:
            from modules.embeddings import update_ghazal_embedding
            update_ghazal_embedding(text_id)
            logger.info(f"✅ Embedding generated for text_id {text_id}")
        except Exception as e:
            logger.warning(f"Embedding failed for text_id {text_id}: {e}")
    
    return {"text_id": text_id, "existing": False}, None