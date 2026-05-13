# modules/stylometry.py
"""
UCPC Stylometry Module
Research-grade stylometric feature extraction
for Urdu Computational Philology

This module extracts:
- lexical richness
- character signatures
- stylistic repetition
- poetic diction
- punctuation behavior
- Urdu orthographic tendencies

Exported Functions:
- generate_stylometric_features (main function)
- extract_stylometric_signature (alias)
- quick_stylometric_profile (fast API version)
- tokenize, normalize_urdu (utilities)
"""

import re
from collections import Counter
from statistics import mean, stdev, median
from typing import List, Dict, Any, Tuple, Optional


# =========================================================
# CONFIGURATION
# =========================================================

URDU_NORMALIZATION_MAP = {
    'ي': 'ی',
    'ك': 'ک',
    'ة': 'ہ',
    'ۀ': 'ہ',
    'ھ': 'ہ',
    'ؤ': 'و',
    'أ': 'ا',
    'إ': 'ا',
    'آ': 'ا',
    'ٱ': 'ا',
    'ى': 'ی',
    '\u200c': ' ',
    '\u200d': ' ',
}

URDU_STOP_WORDS = {
    'ہے', 'کی', 'کے', 'کو', 'میں',
    'سے', 'اور', 'یہ', 'وہ', 'تو',
    'بھی', 'کہ', 'کا', 'ہی', 'نے',
    'تھا', 'تھی', 'تھے', 'ہوں', 'ہو'
}

FUNCTION_WORDS = {
    'نہ', 'ہی', 'تو', 'بھی', 'تک', 'سے', 'پر', 
    'کا', 'کی', 'کے', 'میں', 'تھا', 'تھی', 'ہوں', 'ہے'
}

POETIC_MARKERS = {
    'عشق', 'محبت', 'دل', 'غم', 'یاد', 'رات', 
    'تنہائی', 'خدا', 'زندگی', 'موت', 'اشک', 'آنسو'
}


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_urdu(text: str, remove_diacritics: bool = False) -> str:
    """Normalize Urdu text for consistent analysis"""
    if not text:
        return ""

    text = str(text)

    for old, new in URDU_NORMALIZATION_MAP.items():
        text = text.replace(old, new)

    # Optional diacritic removal
    if remove_diacritics:
        diacritics = r'[\u064B-\u065F\u0670]'
        text = re.sub(diacritics, '', text)

    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)

    return text.strip()


# =========================================================
# TOKENIZATION
# =========================================================

def tokenize(text: str, remove_stopwords: bool = False, remove_short: bool = False) -> List[str]:
    """
    Tokenize Urdu text into words.
    
    Args:
        text: Input text
        remove_stopwords: Filter out common stop words
        remove_short: Remove single-character tokens
    
    Returns:
        List of tokens
    """
    text = normalize_urdu(text)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    tokens = text.split()
    
    if remove_stopwords:
        tokens = [t for t in tokens if t not in URDU_STOP_WORDS]
    
    if remove_short:
        tokens = [t for t in tokens if len(t) > 1]
    
    return [t.strip() for t in tokens if t.strip()]


# =========================================================
# TYPE TOKEN RATIO
# =========================================================

def type_token_ratio(tokens: List[str]) -> float:
    """Calculate Type-Token Ratio (TTR) - basic lexical diversity"""
    if not tokens:
        return 0.0
    unique = len(set(tokens))
    return round(unique / len(tokens), 4)


# =========================================================
# AVERAGE WORD LENGTH
# =========================================================

def average_word_length(tokens: List[str]) -> float:
    """Calculate average word length"""
    if not tokens:
        return 0.0
    lengths = [len(t) for t in tokens]
    return round(mean(lengths), 2)


# =========================================================
# LEXICAL DENSITY
# =========================================================

def lexical_density(tokens: List[str]) -> float:
    """Calculate lexical density (content words / total tokens)"""
    if not tokens:
        return 0.0
    content_words = [t for t in tokens if t not in URDU_STOP_WORDS]
    return round(len(content_words) / len(tokens), 4)


# =========================================================
# MOST COMMON WORDS
# =========================================================

def most_common_words(tokens: List[str], top_n: int = 10) -> List[Tuple[str, int]]:
    """Get most common words excluding stop words"""
    stop_words = URDU_STOP_WORDS
    filtered = [t for t in tokens if t not in stop_words and len(t) > 1]
    freq = Counter(filtered)
    return freq.most_common(top_n)


# =========================================================
# CHARACTER NGRAMS
# =========================================================

def char_ngrams(text: str, n: int = 3, top_n: int = 15) -> List[Tuple[str, int]]:
    """Extract character n-grams for stylometric fingerprinting"""
    text = normalize_urdu(text)
    text = text.replace(" ", "")
    
    if len(text) < n:
        return []
    
    grams = [text[i:i+n] for i in range(len(text) - n + 1)]
    freq = Counter(grams)
    return freq.most_common(top_n)


# =========================================================
# PUNCTUATION PROFILE
# =========================================================

def punctuation_profile(text: str) -> Dict[str, int]:
    """Analyze punctuation usage patterns"""
    puncts = ['۔', '،', '؟', '!', ':', ';', '-']
    profile = {}
    for p in puncts:
        profile[p] = text.count(p)
    return profile


# =========================================================
# VERSE STATISTICS
# =========================================================

def verse_statistics(text: str) -> Dict[str, Any]:
    """Analyze verse-level structure"""
    verses = [v.strip() for v in text.split('\n') if v.strip()]
    
    if not verses:
        return {}
    
    verse_lengths = [len(v.split()) for v in verses]
    
    return {
        "total_verses": len(verses),
        "average_verse_length": round(mean(verse_lengths), 2) if verse_lengths else 0,
        "longest_verse": max(verse_lengths) if verse_lengths else 0,
        "shortest_verse": min(verse_lengths) if verse_lengths else 0,
        "total_couplets": len(verses) // 2
    }


# =========================================================
# LEXICAL REPETITION
# =========================================================

def lexical_repetition(tokens: List[str], min_count: int = 3) -> List[Tuple[str, int]]:
    """Find words that are repeated frequently"""
    freq = Counter(tokens)
    repeated = [(w, c) for w, c in freq.items() if c >= min_count]
    return sorted(repeated, key=lambda x: -x[1])[:15]


# =========================================================
# MAIN ANALYSIS (Primary Export)
# =========================================================

def generate_stylometric_features(text: str) -> Dict[str, Any]:
    """
    Generate comprehensive stylometric features.
    This is the main function for the module.
    """
    text = normalize_urdu(text)
    tokens = tokenize(text)
    unique_tokens = len(set(tokens))
    total_tokens = len(tokens)

    features = {
        # LEXICAL FEATURES
        "lexical_features": {
            "token_count": total_tokens,
            "unique_tokens": unique_tokens,
            "type_token_ratio": type_token_ratio(tokens),
            "average_word_length": average_word_length(tokens),
            "lexical_density": lexical_density(tokens)
        },

        # WORD FREQUENCY
        "dominant_diction": [
            {"word": w, "count": c}
            for w, c in most_common_words(tokens)
        ],

        # CHARACTER STYLE
        "character_signatures": [
            {"ngram": n, "count": c}
            for n, c in char_ngrams(text)
        ],

        # PUNCTUATION
        "punctuation_profile": punctuation_profile(text),

        # VERSE STRUCTURE
        "verse_statistics": verse_statistics(text),

        # REPETITION PATTERNS
        "recurrent_lexicon": [
            {"word": w, "count": c}
            for w, c in lexical_repetition(tokens)
        ],

        # RESEARCH NOTES
        "research_notes": [
            "Character n-grams extracted for stylometric profiling",
            "Lexical repetition may indicate poetic signature",
            "Type-token ratio estimates lexical richness",
            "Verse statistics support computational prosody research"
        ]
    }

    return features


# =========================================================
# ALIASES for API compatibility
# =========================================================

def extract_stylometric_signature(text: str) -> Dict[str, Any]:
    """
    Alias for generate_stylometric_features.
    Maintains compatibility with routes that expect this name.
    """
    return generate_stylometric_features(text)


def quick_stylometric_profile(text: str) -> Dict[str, Any]:
    """
    Simplified stylometric profile for fast API responses.
    Returns only essential metrics.
    """
    text = normalize_urdu(text)
    tokens = tokenize(text)
    verses = [v.strip() for v in text.split('\n') if v.strip()]
    
    return {
        "token_count": len(tokens),
        "unique_tokens": len(set(tokens)),
        "type_token_ratio": type_token_ratio(tokens),
        "average_word_length": average_word_length(tokens),
        "lexical_density": lexical_density(tokens),
        "verse_count": len(verses),
        "couplet_count": len(verses) // 2,
        "average_verse_length": mean([len(v.split()) for v in verses]) if verses else 0,
        "top_character_3grams": char_ngrams(text, n=3, top_n=5)
    }


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":
    sample = """
    دل ہی تو ہے نہ سنگ و خشت، درد سے بھر نہ آئے کیوں
    روئیں گے ہم ہزار بار، کوئی ہمیں سزائے کیوں
    ہم کو ان سے وفا کی ہے امید، جو نہیں جانتے وفا کیا ہے
    رکھتا ہے کس درجہ ہمارا دل، اس بے وفا سے گلہ کیا ہے
    """

    print("=" * 60)
    print("Testing Stylometry Module")
    print("=" * 60)

    # Test main function
    result = generate_stylometric_features(sample)
    print("\n📊 generate_stylometric_features:")
    print(f"  Token count: {result['lexical_features']['token_count']}")
    print(f"  TTR: {result['lexical_features']['type_token_ratio']}")

    # Test alias
    signature = extract_stylometric_signature(sample)
    print("\n📊 extract_stylometric_signature (alias):")
    print(f"  Token count: {signature['lexical_features']['token_count']}")

    # Test quick profile
    quick = quick_stylometric_profile(sample)
    print("\n⚡ quick_stylometric_profile:")
    print(f"  Token count: {quick['token_count']}")
    print(f"  TTR: {quick['type_token_ratio']}")
    print(f"  Top 3-grams: {quick['top_character_3grams']}")

    print("\n✅ Stylometry module ready for production")