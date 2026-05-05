# modules/meter.py
import re
from collections import Counter

# ---------- NORMALIZATION ----------
def normalize_urdu(text):
    text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# ---------- TOKENIZATION ----------
def tokenize(text):
    return re.findall(r'[\u0600-\u06FF]+', text)

# ---------- SYLLABLE ESTIMATION ----------
def count_syllables(word):
    vowels = {'ا', 'آ', 'و', 'ی', 'ے'}
    count = sum(1 for ch in word if ch in vowels)
    return count if count > 0 else 1

# ---------- PATTERN ----------
def pattern_from_line(line):
    words = tokenize(normalize_urdu(line))
    syllables = [count_syllables(w) for w in words]

    pattern = ''.join(['L' if s >= 2 else 'S' for s in syllables])

    return pattern[:16]  # 🔥 increased length


# ---------- KNOWN METERS ----------
METER_MAP = {
    "LSLSLSLS": "Hazaj",
    "SLSLSLSL": "Ramal",
    "LLSLLSLL": "Mutaqarib",
    "LSLLSLL": "Khafif",
}


# ---------- MATCH ----------
def match_meter(patterns):
    """
    Use majority voting across multiple misra
    """
    matches = []

    for pattern in patterns:
        for key in METER_MAP:
            if pattern.startswith(key[:5]):
                matches.append(METER_MAP[key])

    if not matches:
        return "Unknown", 0.0

    most_common = Counter(matches).most_common(1)[0]

    confidence = most_common[1] / len(patterns)

    return most_common[0], round(confidence, 2)


# ---------- MAIN ----------
def detect_meter(verses):
    """
    Use MULTIPLE misra instead of only first
    """
    if not verses:
        return "Unknown", 0.0, ""

    patterns = []

    for v in verses[:5]:  # 🔥 use first 5 couplets
        line = v.get("misra1_urdu", "")
        if line:
            patterns.append(pattern_from_line(line))

    if not patterns:
        return "Unknown", 0.0, ""

    meter, confidence = match_meter(patterns)

    return meter, confidence if confidence > 0.5 else ("Unknown", 0.0)
