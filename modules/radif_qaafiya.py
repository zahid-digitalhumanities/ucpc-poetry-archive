# modules/radif_qaafiya.py
"""
UCPC Radif and Qaafiya Extraction Module
For Urdu ghazal prosodic analysis
"""

import re
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any

# Optional imports with fallbacks
try:
    from modules.meter import detect_meter
except ImportError:
    def detect_meter(verses):
        return None, 0.0, None

try:
    from modules.theme import detect_theme
except ImportError:
    def detect_theme(text):
        return "unknown"


# =========================================================
# NORMALIZATION
# =========================================================

def normalize_line(line: str) -> str:
    """Normalize a single line of Urdu text"""
    if not line:
        return ""
    line = line.strip()
    line = re.sub(r'[،۔!؟,.]', '', line)
    line = re.sub(r'\s+', ' ', line)
    return line


def normalize_urdu(text: str) -> str:
    """Normalize full Urdu text for consistent processing"""
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
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


# =========================================================
# RADIF EXTRACTION
# =========================================================

def extract_radif(second_lines: List[str]) -> Optional[str]:
    """
    Extract radif (refrain) from second lines of verses
    """
    if not second_lines:
        return None
    
    suffix_counts = Counter()
    
    for line in second_lines:
        words = line.split()
        for i in range(len(words)):
            suffix = " ".join(words[i:])
            suffix_counts[suffix] += 1
    
    candidates = [(s, c) for s, c in suffix_counts.items()
                  if c >= len(second_lines) // 2 and len(s.split()) <= 4]
    
    if candidates:
        candidates.sort(key=lambda x: (len(x[0].split()), x[1]), reverse=True)
        return candidates[0][0]
    
    # Fallback: most common last word
    last_words = [line.split()[-1] for line in second_lines if line.split()]
    if not last_words:
        return None
    
    most_common = Counter(last_words).most_common(1)[0]
    if most_common[1] >= len(second_lines) // 2:
        return most_common[0]
    
    return None


# =========================================================
# QAAFIYA EXTRACTION
# =========================================================

def extract_qaafiya(second_lines: List[str], radif: Optional[str]) -> List[str]:
    """
    Extract qaafiya (rhyming scheme) from second lines
    """
    if not second_lines:
        return []
    
    qaafiya_set = set()
    
    for line in second_lines:
        if radif and radif in line:
            parts = line.rsplit(radif, 1)
            if parts[0].strip():
                # Get the last word of the part before radif
                qaafiya_set.add(parts[0].strip().split()[-1])
    
    return list(qaafiya_set)


# =========================================================
# EXTRACT RADIF AND QAAFIYA (Main export function)
# =========================================================

def extract_radif_qaafiya(text: str) -> Dict[str, Any]:
    """
    Extract radif and qaafiya from ghazal text.
    This is the main function for API use.
    
    Args:
        text: Urdu ghazal text
    
    Returns:
        Dictionary with radif, qaafiya, and confidence
    """
    try:
        lines = [normalize_line(l) for l in text.split('\n') if l.strip()]
        
        verses = []
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                verses.append({
                    "misra1_urdu": lines[i],
                    "misra2_urdu": lines[i + 1]
                })
            else:
                verses.append({
                    "misra1_urdu": lines[i],
                    "misra2_urdu": ""
                })
        
        if not verses:
            return {
                "radif": None,
                "qaafiya": [],
                "confidence": 0.0,
                "verse_count": 0
            }
        
        second_lines = [v["misra2_urdu"] for v in verses if v["misra2_urdu"]]
        
        if len(second_lines) < 2:
            return {
                "radif": None,
                "qaafiya": [],
                "confidence": 0.0,
                "verse_count": len(verses)
            }
        
        radif = extract_radif(second_lines)
        qaafiya = extract_qaafiya(second_lines, radif)
        
        # Calculate confidence based on radif presence
        confidence = 0.0
        if radif:
            radif_count = sum(1 for l in second_lines if radif in l)
            confidence = round(radif_count / len(second_lines), 2)
        
        return {
            "radif": radif,
            "qaafiya": qaafiya[:10],  # Limit to top 10
            "confidence": confidence,
            "verse_count": len(verses),
            "couplet_count": len(verses)
        }
    
    except Exception as e:
        print(f"❌ Error extracting radif/qaafiya: {e}")
        return {
            "radif": None,
            "qaafiya": [],
            "confidence": 0.0,
            "error": str(e)
        }


# =========================================================
# PROCESS GHAZAL (Full analysis including meter and theme)
# =========================================================

def process_ghazal(text_id: int, text: str) -> Dict[str, Any]:
    """
    Comprehensive ghazal processing including radif, qaafiya, meter, and theme.
    
    Args:
        text_id: Ghazal ID (0 for raw text)
        text: Urdu ghazal text
    
    Returns:
        Dictionary with full analysis
    """
    try:
        lines = [normalize_line(l) for l in text.split('\n') if l.strip()]
        
        verses = []
        for i in range(0, len(lines), 2):
            if i + 1 < len(lines):
                verses.append({
                    "misra1_urdu": lines[i],
                    "misra2_urdu": lines[i + 1]
                })
            else:
                verses.append({
                    "misra1_urdu": lines[i],
                    "misra2_urdu": ""
                })
        
        if not verses:
            return {
                "text_id": text_id,
                "radif": None,
                "qaafiya": [],
                "confidence": 0.0,
                "meter": None,
                "theme": None,
                "verse_count": 0
            }
        
        second_lines = [v["misra2_urdu"] for v in verses if v["misra2_urdu"]]
        
        if len(second_lines) < 2:
            return {
                "text_id": text_id,
                "radif": None,
                "qaafiya": [],
                "confidence": 0.0,
                "meter": None,
                "theme": None,
                "verse_count": len(verses)
            }
        
        # Extract radif and qaafiya
        radif = extract_radif(second_lines)
        qaafiya = extract_qaafiya(second_lines, radif)
        
        confidence = 0.0
        if radif:
            radif_count = sum(1 for l in second_lines if radif in l)
            confidence = round(radif_count / len(second_lines), 2)
        
        # Extract meter (safe handling)
        meter_name = None
        meter_conf = 0.0
        meter_pattern = None
        
        try:
            meter_result = detect_meter(verses)
            if meter_result:
                if isinstance(meter_result, tuple):
                    if len(meter_result) == 3:
                        meter_name, meter_conf, meter_pattern = meter_result
                    elif len(meter_result) == 2:
                        meter_name, meter_conf = meter_result
                elif isinstance(meter_result, str):
                    meter_name = meter_result
        except Exception as e:
            print(f"⚠️ Meter detection error: {e}")
        
        # Extract theme
        theme = None
        try:
            theme = detect_theme(text)
        except Exception as e:
            print(f"⚠️ Theme detection error: {e}")
        
        return {
            "text_id": text_id,
            "radif": radif,
            "qaafiya": qaafiya[:10],
            "confidence": confidence,
            "meter": meter_name if meter_name and meter_name != "Unknown" else None,
            "meter_confidence": meter_conf,
            "meter_pattern": meter_pattern,
            "theme": theme,
            "verse_count": len(verses),
            "couplet_count": len(verses)
        }
    
    except Exception as e:
        print(f"❌ Error processing ghazal {text_id}: {e}")
        return {
            "text_id": text_id,
            "radif": None,
            "qaafiya": [],
            "confidence": 0.0,
            "meter": None,
            "theme": None,
            "verse_count": 0,
            "error": str(e)
        }


# =========================================================
# SIMPLE EXTRACTOR (Alias for backward compatibility)
# =========================================================

def extract_radif_and_qaafiya(text: str) -> Dict[str, Any]:
    """Alias for extract_radif_qaafiya"""
    return extract_radif_qaafiya(text)


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
    print("Testing Radif/Qaafiya Extraction")
    print("=" * 60)
    
    result = extract_radif_qaafiya(sample)
    print(f"Radif: {result['radif']}")
    print(f"Qaafiya: {result['qaafiya']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Verse Count: {result['verse_count']}")
    
    print("\n" + "=" * 60)
    print("Testing process_ghazal")
    print("=" * 60)
    
    full_result = process_ghazal(0, sample)
    print(f"Radif: {full_result['radif']}")
    print(f"Qaafiya: {full_result['qaafiya']}")
    print(f"Confidence: {full_result['confidence']}")
    print(f"Meter: {full_result['meter']}")
    print(f"Theme: {full_result['theme']}")