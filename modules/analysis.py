# modules/analysis.py - UPDATED & COMPLETE
"""
Advanced analysis functions for Urdu ghazals.
Detects radif, qaafiya, meter, behr, and extracts verses.
"""

import re

def clean_line(line):
    """Remove punctuation and normalize whitespace"""
    line = line.strip()
    line = re.sub(r"[،۔!?]", "", line)
    return line

def split_verses(text):
    """Ghazal text ko verses mein divide karein"""
    if not text:
        return []
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    verses = []
    
    i = 0
    while i < len(lines):
        if i + 1 < len(lines):
            verses.append((lines[i], lines[i + 1]))
            i += 2
        else:
            verses.append((lines[i], ""))
            i += 1
    
    return verses

def detect_radif_qafia(text):
    """Detect radif and qaafiya from ghazal lines"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    if len(lines) < 4:
        return None, None

    # Collect second misras only (couplets: line2, line4, line6...)
    second_misras = []
    for i in range(1, len(lines), 2):
        try:
            second_misras.append(clean_line(lines[i]))
        except:
            continue

    # Get last words of each second misra
    endings = []
    for l in second_misras:
        words = l.split()
        if words:
            endings.append(words[-1])

    # Find radif (word appearing at least twice)
    radif = None
    freq = {}
    for w in endings:
        freq[w] = freq.get(w, 0) + 1
    for w, count in freq.items():
        if count >= 2:
            radif = w
            break

    # Collect qaafiya (second-last words from second misras where last word = radif)
    qafia = set()
    if radif:
        for l in second_misras:
            words = l.split()
            if len(words) >= 2 and words[-1] == radif:
                qafia.add(words[-2])

    return radif, list(qafia)

def detect_meter(text):
    """Simple meter detection based on total character length"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    total_len = sum(len(l) for l in lines)
    if total_len < 120:
        return "short"
    elif total_len < 250:
        return "medium"
    else:
        return "long"

def detect_behr(text):
    """Behr (poetic meter) pattern detection"""
    verses = split_verses(text)
    if not verses:
        return "unknown"
    
    patterns = []
    for verse in verses[:3]:
        if verse[1]:
            words = verse[1].split()[:3]
            pattern = []
            for word in words:
                # Count potential syllables
                syllables = sum(1 for c in word if c in 'ا و ی ئ ء آ')
                syllables = max(syllables, 1)
                pattern.append(str(syllables))
            if pattern:
                patterns.append('-'.join(pattern))
    
    if len(patterns) >= 2 and all(p == patterns[0] for p in patterns):
        return f"regular_{patterns[0]}"
    else:
        return "irregular"

def extract_first_line(text):
    """پہلی مصرع نکالیں"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    return lines[0] if lines else ""

def count_verses(text):
    """اشعار کی تعداد"""
    return len(split_verses(text))

def extract_all_verses(text):
    """تمام اشعار کو list of dicts mein convert karein"""
    verses = split_verses(text)
    result = []
    for i, (m1, m2) in enumerate(verses, 1):
        result.append({
            'position': i,
            'misra1': m1,
            'misra2': m2
        })
    return result

def analyze_poetry(text):
    """Complete poetry analysis"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    radif, qafia = detect_radif_qafia(text)
    meter = detect_meter(text)
    behr = detect_behr(text)
    verses = extract_all_verses(text)
    first_line = extract_first_line(text)
    
    qafia_str = ",".join(qafia) if qafia else ""
    
    return {
        'verses': verses,
        'verse_count': len(verses),
        'radif': radif if radif else "",
        'qafia': qafia_str,
        'meter': meter,
        'behr': behr,
        'first_line': first_line
    }

def roman_urdu_to_urdu(roman_text):
    """Roman Urdu to Urdu conversion"""
    mapping = {
        'a': 'ا', 'b': 'ب', 'p': 'پ', 't': 'ت', 's': 'س',
        'j': 'ج', 'ch': 'چ', 'h': 'ہ', 'k': 'ک', 'd': 'د',
        'r': 'ر', 'z': 'ز', 'gh': 'غ', 'f': 'ف', 'q': 'ق',
        'l': 'ل', 'm': 'م', 'n': 'ن', 'w': 'و', 'y': 'ی',
        'aa': 'آ', 'ee': 'ی', 'oo': 'و', 'sh': 'ش', 'kh': 'خ'
    }
    
    result = []
    words = roman_text.lower().split()
    for word in words:
        converted = word
        for rom, ur in mapping.items():
            converted = converted.replace(rom, ur)
        result.append(converted)
    
    return ' '.join(result)