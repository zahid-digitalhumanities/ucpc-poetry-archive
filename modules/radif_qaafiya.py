import re
from collections import Counter
from modules.meter import detect_meter
from modules.theme import detect_theme

def normalize_line(line):
    line = line.strip()
    line = re.sub(r'[،۔!؟,.]', '', line)
    line = re.sub(r'\s+', ' ', line)
    return line

def extract_radif(second_lines):
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
    last_words = [line.split()[-1] for line in second_lines if line.split()]
    if not last_words:
        return None
    most_common = Counter(last_words).most_common(1)[0]
    if most_common[1] >= len(second_lines) // 2:
        return most_common[0]
    return None

def extract_qaafiya(second_lines, radif):
    qaafiya_set = set()
    for line in second_lines:
        if radif and radif in line:
            parts = line.rsplit(radif, 1)
            if parts[0].strip():
                qaafiya_set.add(parts[0].strip().split()[-1])
    return list(qaafiya_set)

def process_ghazal(text_id, text):
    try:
        lines = [normalize_line(l) for l in text.split('\n') if l.strip()]
        verses = []
        for i in range(0, len(lines), 2):
            if i+1 < len(lines):
                verses.append({"misra1_urdu": lines[i], "misra2_urdu": lines[i+1]})
            else:
                verses.append({"misra1_urdu": lines[i], "misra2_urdu": ""})
        if not verses:
            return {"text_id": text_id, "radif": None, "qaafiya": [], "confidence": 0.0, "meter": None, "theme": None}
        second_lines = [v["misra2_urdu"] for v in verses if v["misra2_urdu"]]
        if len(second_lines) < 2:
            return {"text_id": text_id, "radif": None, "qaafiya": [], "confidence": 0.0, "meter": None, "theme": None}
        radif = extract_radif(second_lines)
        qaafiya = extract_qaafiya(second_lines, radif)
        confidence = sum(1 for l in second_lines if radif and radif in l) / len(second_lines) if radif else 0.0

        # ✅ SAFE METER HANDLING (handles 2 or 3 return values)
        meter_name, meter_conf, meter_pattern = None, 0.0, None
        try:
            meter_result = detect_meter(verses)
            if isinstance(meter_result, tuple):
                if len(meter_result) == 3:
                    meter_name, meter_conf, meter_pattern = meter_result
                elif len(meter_result) == 2:
                    meter_name, meter_conf = meter_result
                    meter_pattern = None
                else:
                    meter_name, meter_conf, meter_pattern = None, 0.0, None
            else:
                meter_name, meter_conf, meter_pattern = None, 0.0, None
        except Exception as e:
            print(f"⚠️ Meter error: {e}")

        theme = detect_theme(text)

        return {
            "text_id": text_id,
            "radif": radif,
            "qaafiya": qaafiya,
            "confidence": round(confidence, 2),
            "meter": meter_name if meter_name and meter_name != "Unknown" else None,
            "theme": theme
        }
    except Exception as e:
        print(f"❌ Error processing {text_id}: {e}")
        return {"text_id": text_id, "radif": None, "qaafiya": [], "confidence": 0.0, "meter": None, "theme": None}