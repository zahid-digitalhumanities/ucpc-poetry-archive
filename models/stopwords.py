# models/stopwords.py
COMMON_STOPWORDS = {
    "tum", "hum", "woh", "yeh", "dil", "ishq", "raat", "mein", "hai", 
    "aap", "main", "tere", "mera", "tera", "koi", "kya", "na", "se",
    "aur", "bhi", "to", "tha", "thi", "the", "ki", "ke", "ko",
    "se", "par", "pe", "tak", "liye", "baad", "pehle"
}

def is_generic_query(keyword):
    """Return True if query is too broad (stopword-only or very short)."""
    tokens = keyword.split()
    if len(tokens) <= 2 and all(t in COMMON_STOPWORDS for t in tokens):
        return True
    if len(keyword) < 3 and keyword in COMMON_STOPWORDS:
        return True
    return False

def suggest_alternative(keyword):
    """Return a helpful suggestion for generic queries."""
    suggestions = {
        "tum": "tum aaye, tum se, tumhare",
        "hum": "hum dono, hum na the, hum bhi",
        "woh": "woh log, woh din, woh baat",
        "dil": "dil hi to hai, dil dhadakta hai",
        "ishq": "ishq ne, ishq mein, ishq hai",
        "raat": "raat gayi, raat dhal gayi",
    }
    return suggestions.get(keyword.lower(), "Try adding more words (e.g., 'tum aaye', 'woh log')")