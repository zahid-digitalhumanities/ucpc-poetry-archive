# modules/theme.py

import re
from collections import Counter

# =========================================================
# ADVANCED DH THEMATIC LEXICON
# =========================================================

THEMES = {
    "love": {
        "label": "Love / Romance",
        "keywords": [
            "محبت", "عشق", "دل", "یار", "جان",
            "چاہت", "وفا", "ہجر", "وصال",
            "محبوب", "عاشق", "پیار", "نگاہ"
        ]
    },

    "pain": {
        "label": "Pain / Grief",
        "keywords": [
            "درد", "غم", "اداسی", "تنہائی",
            "آنسو", "رنج", "تکلیف",
            "فراق", "جدائی", "غمگین"
        ]
    },

    "philosophy": {
        "label": "Philosophy / Existential",
        "keywords": [
            "زندگی", "موت", "وقت",
            "حقیقت", "فنا", "بقا",
            "وجود", "کائنات", "قسمت"
        ]
    },

    "spiritual": {
        "label": "Spiritual / Sufi",
        "keywords": [
            "خدا", "رب", "دعا",
            "عبادت", "روح", "ایمان",
            "صوفی", "جنت", "نماز"
        ]
    },

    "nature": {
        "label": "Nature / Environment",
        "keywords": [
            "چاند", "رات", "دن",
            "ہوا", "بارش", "دریا",
            "پھول", "صحرا", "بادل"
        ]
    },

    "wine": {
        "label": "Wine / Classical Symbolism",
        "keywords": [
            "مے", "ساقی", "شراب",
            "پیمانہ", "میخانہ",
            "جام", "نشہ"
        ]
    }
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(text):

    text = text.lower()

    text = re.sub(r'[^\u0600-\u06FF\s]', ' ', text)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# =========================================================
# TOKENIZER
# =========================================================

def tokenize(text):

    return re.findall(r'[\u0600-\u06FF]+', text)


# =========================================================
# EXTRACT THEME KEYWORDS
# =========================================================

def extract_theme_keywords(text):

    text = normalize(text)

    words = tokenize(text)

    found = []

    for theme_data in THEMES.values():

        for kw in theme_data['keywords']:

            if kw in words:
                found.append(kw)

    return list(dict.fromkeys(found))


# =========================================================
# MAIN THEME DETECTOR
# =========================================================

def detect_theme(text):

    text = normalize(text)

    words = tokenize(text)

    scores = {}

    for theme_name, theme_data in THEMES.items():

        score = 0

        for kw in theme_data['keywords']:

            score += words.count(kw)

        scores[theme_name] = score

    best_theme = max(scores, key=scores.get)

    best_score = scores[best_theme]

    # threshold
    if best_score < 2:
        return "unknown"

    return best_theme


# =========================================================
# MULTI THEME SUPPORT
# =========================================================

def detect_multiple_themes(text, top_n=3):

    text = normalize(text)

    words = tokenize(text)

    scores = {}

    for theme_name, theme_data in THEMES.items():

        score = 0

        for kw in theme_data['keywords']:

            score += words.count(kw)

        scores[theme_name] = score

    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    results = []

    for theme, score in ranked[:top_n]:

        if score > 0:

            results.append({
                "theme": theme,
                "label": THEMES[theme]['label'],
                "score": score
            })

    return results