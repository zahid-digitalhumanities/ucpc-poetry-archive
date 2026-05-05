# modules/theme.py
import re
from collections import Counter

# Expanded + weighted themes
THEMES = {
    "love": ["محبت", "عشق", "دل", "یار", "جان", "چاہت", "وفا", "ہجر", "وصال"],
    "pain": ["درد", "غم", "اداسی", "تنہائی", "آنسو", "رنج", "تکلیف"],
    "philosophy": ["زندگی", "موت", "وقت", "حقیقت", "فنا", "بقا", "وجود"],
    "spiritual": ["خدا", "رب", "دعا", "عبادت", "روح", "ایمان"],
    "nature": ["چاند", "رات", "دن", "ہوا", "بارش", "دریا", "پھول"],
    "wine": ["مے", "ساقی", "شراب", "پیمانہ", "میخانہ"],
}

# ---------- NORMALIZATION ----------
def normalize(text):
    text = text.lower()
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ---------- TOKENIZATION ----------
def tokenize(text):
    return re.findall(r'[\u0600-\u06FF]+', text)

# ---------- MAIN ----------

def detect_theme(text):
    words = text.split()
    scores = {}

    for theme, keywords in THEMES.items():
        score = sum(2 for w in words if w in keywords)  # weight = 2
        scores[theme] = score

    best_theme, best_score = max(scores.items(), key=lambda x: x[1])

    # 🚀 NEW: threshold
    if best_score < 2:
        return "unknown"

    return best_theme