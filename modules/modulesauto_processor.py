# modules/auto_processor.py
import re
from collections import Counter

# ------------------------------------------------------------
# Normalization
# ------------------------------------------------------------
def normalize_urdu(text: str) -> str:
    """Normalize Urdu text by removing extra spaces."""
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)
    return text

# ------------------------------------------------------------
# Splitting ghazal into verses (misra pairs)
# ------------------------------------------------------------
def split_ghazal(ghazal_text: str):
    """Split a ghazal text into a list of (misra1, misra2) pairs."""
    lines = [l.strip() for l in ghazal_text.split('\n') if l.strip()]
    verses = []
    for i in range(0, len(lines), 2):
        misra1 = lines[i]
        misra2 = lines[i + 1] if i + 1 < len(lines) else ""
        verses.append((misra1, misra2))
    return verses

# ------------------------------------------------------------
# Radif detection
# ------------------------------------------------------------
def detect_radif(verses):
    """
    Detect radif – the last word of the second misra that repeats across most verses.
    Returns the most common ending word or None.
    """
    endings = []
    for _, misra2 in verses:
        if misra2:
            words = misra2.split()
            if words:
                endings.append(words[-1])
    if endings:
        # Count occurrences
        cnt = Counter(endings)
        # Return the most common (could be ambiguous; we take the top)
        return cnt.most_common(1)[0][0]
    return None

# ------------------------------------------------------------
# Qaafiya detection
# ------------------------------------------------------------
def detect_qaafiya(verses, radif):
    """
    Detect qaafiya – the rhyming word just before radif (if radif exists),
    else the last word of second misra.
    Returns the most common candidate or None.
    """
    candidates = []
    for _, misra2 in verses:
        if not misra2:
            continue
        words = misra2.split()
        if radif and len(words) >= 2 and words[-1] == radif:
            candidates.append(words[-2])
        elif not radif and words:
            # If no radif, take the last word as potential qaafiya
            candidates.append(words[-1])
    if candidates:
        cnt = Counter(candidates)
        return cnt.most_common(1)[0][0]
    return None

# ------------------------------------------------------------
# Simple beher detection (placeholder)
# ------------------------------------------------------------
def detect_beher(verses):
    """
    Placeholder for meter detection. Currently returns a rough classification
    based on average syllable count per misra.
    """
    if not verses:
        return "unknown"

    # Count syllables roughly by counting Urdu vowel letters (ا و ی ئ ء آ)
    def count_syllables(text):
        vowels = 'ا و ی ئ ء آ'
        return sum(1 for c in text if c in vowels)

    lengths = []
    for misra1, misra2 in verses:
        if misra1:
            lengths.append(count_syllables(misra1))
        if misra2:
            lengths.append(count_syllables(misra2))

    if not lengths:
        return "unknown"
    avg = sum(lengths) / len(lengths)
    if avg < 5:
        return "short (khafif)"
    elif avg < 9:
        return "medium (hazaj)"
    else:
        return "long (muzari)"


# ------------------------------------------------------------
# Main processing function
# ------------------------------------------------------------
def process_ghazal(ghazal_text):
    """
    Process a raw ghazal text and return a dictionary containing:
        - verses: list of (misra1, misra2)
        - radif: detected radif (or None)
        - qaafiya: detected qaafiya (or None)
        - beher: detected meter (or "unknown")
    """
    ghazal_text = normalize_urdu(ghazal_text)
    verses = split_ghazal(ghazal_text)

    radif = detect_radif(verses)
    qaafiya = detect_qaafiya(verses, radif)
    beher = detect_beher(verses)

    return {
        "verses": verses,
        "radif": radif,
        "qaafiya": qaafiya,
        "beher": beher
    }


# ------------------------------------------------------------
# Optional: Test with a SQL query (user can run manually)
# ------------------------------------------------------------
def test_with_sample_text():
    """
    Test the functions on a small sample ghazal.
    To test with a real SQL query, you can run:
        SELECT text_urdu FROM texts LIMIT 1;
    and then pass the result to process_ghazal().
    """
    sample = """دلِ ناداں تجھے ہوا کیا ہے
آخر اس درد کی دوا کیا ہے

ہم کو معلوم ہے جنت کی حقیقت
لیکن دل کے بہلنے کو غزل خواہ ہے"""
    result = process_ghazal(sample)
    print("Verses:", result["verses"])
    print("Radif:", result["radif"])
    print("Qaafiya:", result["qaafiya"])
    print("Beher:", result["beher"])

if __name__ == "__main__":
    test_with_sample_text()