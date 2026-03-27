# Very basic Roman to Urdu mapping (extend as needed)
ROMAN_MAP = {
    'a': 'ا', 'b': 'ب', 'p': 'پ', 't': 'ت', 's': 'س', 'j': 'ج', 'ch': 'چ',
    'h': 'ہ', 'kh': 'خ', 'd': 'د', 'z': 'ز', 'r': 'ر', 'sh': 'ش', 'gh': 'غ',
    'f': 'ف', 'q': 'ق', 'k': 'ک', 'g': 'گ', 'l': 'ل', 'm': 'م', 'n': 'ن',
    'v': 'و', 'w': 'و', 'y': 'ی', 'e': 'ے', 'i': 'ی', 'u': 'و', 'o': 'و',
    'aa': 'آ', 'ee': 'ی', 'oo': 'و'
}

def roman_to_urdu(text):
    """Convert Roman Urdu to Urdu script (approximate)"""
    text = text.lower()
    # Sort keys by length descending to handle multi‑char first
    for rom in sorted(ROMAN_MAP.keys(), key=len, reverse=True):
        text = text.replace(rom, ROMAN_MAP[rom])
    return text