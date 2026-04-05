import re

def normalize_roman(text):
    text = text.lower().strip()
    text = re.sub(r'[^a-z\s]', '', text)
    text = text.replace("aa", "a")
    text = text.replace("ee", "i")
    text = text.replace("oo", "u")
    text = re.sub(r'\s+', ' ', text)
<<<<<<< HEAD
    return text
=======
    return text
>>>>>>> a881c909ad9bd51fcab3855c8cea05c524f253d2
