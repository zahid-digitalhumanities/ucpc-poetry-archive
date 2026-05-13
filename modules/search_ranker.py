# modules/search_ranker.py
"""
Weighted search ranking for Urdu ghazals.
"""

import re
from difflib import SequenceMatcher

# =========================
# MATCH WEIGHTS
# =========================

WEIGHTS = {
    "exact_matla": 100,
    "exact_line": 95,
    "phrase_match": 80,
    "semantic_match": 65,
    "roman_match": 50,
    "partial_match": 30,
    "single_token": 15
}

# =========================
# TEXT NORMALIZATION
# =========================

def normalize_text(text: str) -> str:
    """Normalize Urdu text for matching."""
    if not text:
        return ""

    text = text.lower().strip()

    replacements = {
        "أ": "ا",
        "آ": "ا",
        "إ": "ا",
        "ة": "ہ",
        "ي": "ی",
        "ك": "ک",
        "ـ": "",          # tatweel
        "ٰ": "",          # superscript alef
        "ً": "",          # diacritics
        "ٌ": "",
        "ٍ": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    # Remove extra spaces and punctuation
    text = re.sub(r'[،۔!؟,:;]', '', text)
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


# =========================
# SIMILARITY
# =========================

def similarity(a: str, b: str) -> float:
    """Return a similarity ratio between two strings."""
    return SequenceMatcher(None, a, b).ratio()


# =========================
# GET MATLA (First couplet)
# =========================

def get_matla_from_text(full_text: str) -> str:
    """Extract first couplet (first 2 lines) from ghazal text."""
    if not full_text:
        return ""
    lines = [l.strip() for l in full_text.split('\n') if l.strip()]
    if len(lines) >= 2:
        return f"{lines[0]} {lines[1]}"
    return full_text


# =========================
# SEARCH TYPE DETECTION
# =========================

def detect_match_type(query: str, matla: str, full_text: str) -> str:
    """
    Determine the type of match between query and ghazal.
    """
    query_n = normalize_text(query)
    matla_n = normalize_text(matla)
    full_n = normalize_text(full_text)
    
    # Get first 50 chars of matla for partial matching
    matla_prefix = matla_n[:100] if len(matla_n) > 100 else matla_n
    
    # Exact matla match (full matla or significant portion)
    if query_n == matla_n:
        return "exact_matla"
    
    # Query is contained in matla (exact line)
    if query_n in matla_n:
        return "exact_line"
    
    # Query matches beginning of matla
    if matla_n.startswith(query_n) or query_n in matla_prefix:
        return "exact_line"
    
    # Phrase match (query appears anywhere in full text)
    if query_n in full_n:
        return "phrase_match"
    
    # Fuzzy semantic match for matla
    sim_with_matla = similarity(query_n[:100], matla_n[:200])
    if sim_with_matla > 0.7:
        return "semantic_match"
    
    # Fuzzy match with full text
    sim_with_full = similarity(query_n, full_n[:500])
    if sim_with_full > 0.6:
        return "semantic_match"
    
    # Partial token match
    query_tokens = query_n.split()
    if len(query_tokens) > 1:
        matches = sum(1 for t in query_tokens if t in full_n)
        if matches >= len(query_tokens) * 0.6:
            return "partial_match"
    
    return "single_token"


# =========================
# SCORE SEARCH RESULT
# =========================

def score_result(query: str, matla: str, full_text: str) -> dict:
    """
    Score a single search result based on match type and fuzzy similarity.
    """
    # Get matla if not provided
    if not matla and full_text:
        matla = get_matla_from_text(full_text)
    
    match_type = detect_match_type(query, matla, full_text)
    base_score = WEIGHTS.get(match_type, 0)
    
    query_n = normalize_text(query)
    matla_n = normalize_text(matla)
    
    # Bonus for high similarity
    sim_bonus = similarity(query_n, matla_n) * 20
    
    # Additional bonus for shorter queries matching exactly
    if len(query_n) > 10 and query_n in matla_n:
        sim_bonus += 10
    
    final_score = round(base_score + sim_bonus, 2)
    
    return {
        "match_type": match_type,
        "score": final_score
    }