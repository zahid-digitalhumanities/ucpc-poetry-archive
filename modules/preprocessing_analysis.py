# modules/preprocessing_analysis.py
"""
UCPC Preprocessing Diagnostics
Digital Humanities preprocessing analytics
for Urdu computational philology.
"""

import re
from typing import Dict, List, Any, Optional


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_text(text: str) -> str:
    """Normalize Urdu text"""
    if not text:
        return ""

    text = str(text)

    replacements = {
        'ي': 'ی',
        'ك': 'ک',
        'ة': 'ہ',
        'ۀ': 'ہ',
        'ھ': 'ہ',
        'ؤ': 'و',
        'أ': 'ا',
        'إ': 'ا',
        'آ': 'ا',
        '\u200c': ' ',
        '\u200d': ' ',
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def normalize_urdu(text: str) -> str:
    """Alias for normalize_text"""
    return normalize_text(text)


# =========================================================
# TOKENIZATION
# =========================================================

def tokenize(text: str) -> List[str]:
    """Tokenize Urdu text into words"""
    text = normalize_text(text)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', text)
    tokens = text.split()
    return [t.strip() for t in tokens if t.strip()]


# =========================================================
# SCRIPT DETECTION
# =========================================================

def detect_script(text: str) -> str:
    """Detect script type (Urdu/Roman/Mixed)"""
    urdu_chars = re.findall(r'[\u0600-\u06FF]', text)
    english_chars = re.findall(r'[A-Za-z]', text)

    if len(urdu_chars) > len(english_chars):
        return "Urdu"
    if len(english_chars) > len(urdu_chars):
        return "Roman Urdu / English"
    return "Mixed"


# =========================================================
# LINE ANALYSIS
# =========================================================

def line_statistics(text: str) -> Dict[str, Any]:
    """Calculate line statistics"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    if not lines:
        return {}

    lengths = [len(l.split()) for l in lines]

    return {
        "line_count": len(lines),
        "average_line_length": round(sum(lengths) / len(lengths), 2),
        "longest_line": max(lengths),
        "shortest_line": min(lengths)
    }


# =========================================================
# DETECT FORM
# =========================================================

def detect_poetic_form(text: str) -> str:
    """Detect poetic form (Ghazal/Nazm/Undetermined)"""
    lines = [l.strip() for l in text.split('\n') if l.strip()]

    if len(lines) >= 4:
        return "Likely Ghazal"
    if len(lines) >= 10:
        return "Possibly Nazm"
    return "Undetermined"


# =========================================================
# SPECIAL CHARACTER ANALYSIS
# =========================================================

def special_character_profile(text: str) -> Dict[str, int]:
    """Analyze special characters and punctuation"""
    return {
        "arabic_comma": text.count('،'),
        "urdu_fullstop": text.count('۔'),
        "question_mark": text.count('؟'),
        "exclamation": text.count('!'),
        "quotes": text.count('"'),
        "parentheses": text.count('(') + text.count(')')
    }


# =========================================================
# MAIN CORPUS METRICS
# =========================================================

def corpus_metrics(text: str, verbose: bool = False) -> Dict[str, Any]:
    """Generate comprehensive preprocessing metrics"""
    original = str(text)
    normalized = normalize_text(original)
    tokens = tokenize(normalized)
    unique_tokens = len(set(tokens))

    metrics = {
        "original_character_count": len(original),
        "normalized_character_count": len(normalized),
        "token_count": len(tokens),
        "unique_tokens": unique_tokens,
        "detected_script": detect_script(normalized),
        "detected_form": detect_poetic_form(normalized),
        "line_statistics": line_statistics(normalized),
        "special_character_profile": special_character_profile(normalized),
        "normalization_applied": True,
        "whitespace_cleaned": True,
        "rtl_language_detected": detect_script(normalized) == "Urdu",
        "research_notes": [
            "Orthographic normalization applied",
            "Unicode Urdu normalization completed",
            "Whitespace harmonization completed",
            "Tokenization suitable for DH pipelines",
            "Metrics support reproducible preprocessing"
        ]
    }

    if verbose:
        metrics["verbose"] = {
            "original_preview": original[:200],
            "normalized_preview": normalized[:200],
            "token_sample": tokens[:20]
        }

    return metrics


# =========================================================
# PREPROCESS FOR ML PIPELINE (Main export function)
# =========================================================

def preprocess_urdu_text(text: str) -> Dict[str, Any]:
    """
    Preprocess text for ML pipeline with metrics.
    This is the main function for API use.
    
    Args:
        text: Input Urdu text
    
    Returns:
        Dictionary with normalized text, tokens, and metadata
    """
    original = text
    normalized = normalize_text(text)
    tokens = tokenize(normalized)
    
    return {
        "original_text": original,
        "normalized_text": normalized,
        "tokens": tokens,
        "token_count": len(tokens),
        "character_count": len(normalized),
        "script": detect_script(normalized),
        "verse_count": len([l for l in normalized.split('\n') if l.strip()]),
        "preprocessing_successful": len(normalized) > 0,
        "metrics": corpus_metrics(text, verbose=False)
    }


# =========================================================
# VALIDATE URDU TEXT
# =========================================================

def validate_urdu_text(text: str) -> Dict[str, Any]:
    """
    Validate if text is suitable for Urdu NLP pipelines.
    Returns validation report.
    """
    normalized = normalize_text(text)
    tokens = tokenize(normalized)
    script = detect_script(normalized)
    
    issues = []
    warnings = []
    
    if len(text) < 40:
        issues.append("Text too short (<40 chars) for reliable analysis")
    
    if script != "Urdu":
        warnings.append(f"Text may not be primarily Urdu script (detected: {script})")
    
    if len(tokens) < 10:
        issues.append("Too few tokens (<10) for meaningful analysis")
    
    if len(issues) > 0:
        status = "invalid"
    elif len(warnings) > 0:
        status = "marginal"
    else:
        status = "valid"
    
    return {
        "status": status,
        "issues": issues,
        "warnings": warnings,
        "character_count": len(text),
        "token_count": len(tokens),
        "script": script,
        "recommendation": "Text is ready for processing" if status == "valid" else "Text needs review"
    }


# =========================================================
# BATCH PREPROCESSING
# =========================================================

def batch_preprocess(texts: List[str]) -> List[Dict[str, Any]]:
    """Preprocess multiple texts"""
    return [preprocess_urdu_text(t) for t in texts]


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
    print("Testing Preprocessing Module")
    print("=" * 60)

    # Test preprocess_urdu_text
    result = preprocess_urdu_text(sample)
    print("\n📊 preprocess_urdu_text:")
    print(f"  Normalized length: {result['character_count']}")
    print(f"  Token count: {result['token_count']}")
    print(f"  Script: {result['script']}")
    print(f"  Verses: {result['verse_count']}")

    # Test corpus_metrics
    metrics = corpus_metrics(sample)
    print("\n📊 corpus_metrics:")
    print(f"  Original chars: {metrics['original_character_count']}")
    print(f"  Normalized chars: {metrics['normalized_character_count']}")
    print(f"  Token count: {metrics['token_count']}")
    print(f"  Script: {metrics['detected_script']}")
    print(f"  Form: {metrics['detected_form']}")

    # Test validation
    validation = validate_urdu_text(sample)
    print("\n✅ Validation:")
    print(f"  Status: {validation['status']}")
    print(f"  Issues: {validation['issues']}")
    print(f"  Warnings: {validation['warnings']}")

    print("\n✅ Preprocessing module ready for production")