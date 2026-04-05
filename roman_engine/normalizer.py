import re

def normalize_roman(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z\s]', '', text)
    text = text.replace("aa", "a")
    text = text.replace("ee", "i")
    text = text.replace("oo", "u")
    text = re.sub(r'\s+', ' ', text)
    return text
