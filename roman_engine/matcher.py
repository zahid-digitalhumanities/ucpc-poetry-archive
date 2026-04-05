from modules.roman_engine.normalizer import normalize_roman
from modules.roman_engine.dictionary import ROMAN_URDU_DICT

def roman_to_urdu(word):
    word = normalize_roman(word)
    if word in ROMAN_URDU_DICT:
        return ROMAN_URDU_DICT[word]
    return []

def process_query(query):
    if not query:
        return ""
    words = query.split()
    result_words = []
    for w in words:
        matches = roman_to_urdu(w)
        if matches:
            result_words.append(matches[0])
        else:
            result_words.append(w)
<<<<<<< HEAD
    return " ".join(result_words)
=======
    return " ".join(result_words)
>>>>>>> a881c909ad9bd51fcab3855c8cea05c524f253d2
