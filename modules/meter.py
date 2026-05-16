# modules/meter.py

import re

# ================= NORMALIZATION =================
def normalize_urdu(text):
    if not text:
        return ""
    replacements = {
        "ي": "ی",
        "ك": "ک",
        "ه": "ہ",
        "ة": "ہ",
        "أ": "ا",
        "إ": "ا",
        "ؤ": "و",
        "ئ": "ی"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.strip()


# ================= TOKENIZATION =================
def tokenize_urdu(text):
    return re.findall(r'[\u0600-\u06FF]+', text)


# ================= SYLLABLE ESTIMATION =================
def count_syllables(word):
    """
    Approximate syllable count for Urdu.
    """
    vowels = {'ا', 'آ', 'و', 'ی', 'ے', 'َ', 'ِ', 'ُ'}
    count = 0
    for ch in word:
        if ch in vowels:
            count += 1

    # fallback
    if count == 0 and word:
        count = 1

    return count


# ================= PATTERN GENERATION =================
def generate_meter_pattern(misra):
    """
    Convert misra into L/S pattern.
    """
    misra = normalize_urdu(misra)
    words = tokenize_urdu(misra)

    if not words:
        return ""

    syllables = [count_syllables(w) for w in words]

    # Convert to L/S
    pattern = ''.join(['L' if s >= 2 else 'S' for s in syllables])

    # Normalize length (limit for stability)
    return pattern[:12]


# ================= METER CLASSIFICATION =================
METER_MAP = {
    # Experimental mappings – expand later with real data
    "LSLSLSLS": "Hazaj (مفاعیلن)",
    "SLSLSLSL": "Ramal (فاعلاتن)",
    "LLSLLSLL": "Mutaqarib (فعولن)",
    "LSLLSLL": "Khafif (مستفعلن)",
}


def classify_meter(pattern):
    """
    Match pattern to known meters.
    """
    if not pattern:
        return "Unknown", 0.0

    # Exact match
    if pattern in METER_MAP:
        return METER_MAP[pattern], 0.8

    # Partial similarity (soft match)
    for key in METER_MAP:
        if pattern.startswith(key[:4]):
            return METER_MAP[key], 0.5

    return "Unknown", 0.3


# ================= MAIN DETECTOR =================
def detect_meter(verses):
    """
    Detect meter from FIRST MISRA (standard approach).
    verses: list of dicts with misra1_urdu
    """
    if not verses:
        return "Unknown", 0.0, ""

    first_misra = verses[0].get("misra1_urdu", "")

    if not first_misra.strip():
        return "Unknown", 0.0, ""

    pattern = generate_meter_pattern(first_misra)

    meter, confidence = classify_meter(pattern)

    return meter, confidence, pattern