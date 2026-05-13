import re

def normalize_urdu(text):
    if not text:
        return ""
    text = text.strip()
    # Arabic → Urdu normalization
    text = text.replace("ي", "ی")
    text = text.replace("ك", "ک")
    text = text.replace("ة", "ہ")
    # Remove punctuation (keep Urdu chars, spaces, alphanumerics)
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()