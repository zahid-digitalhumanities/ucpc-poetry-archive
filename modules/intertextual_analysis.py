"""
UCPC Intertextual Analysis Module
Research-grade Digital Humanities infrastructure for Urdu poetic intertextuality detection.

Detects:
- lexical overlap
- thematic resonance
- shared imagery
- semantic reuse
- stylistic affinity
"""

import re
from collections import Counter
from difflib import SequenceMatcher


class UrduTextPreprocessor:
    """Simple preprocessor for Urdu text."""

    def normalize_urdu(self, text):
        if not text:
            return ""
        text = str(text)
        replacements = {"ي": "ی", "ك": "ک", "ة": "ہ", "أ": "ا", "إ": "ا", "آ": "آ"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()


class IntertextualAnalyzer:
    def __init__(self):
        self.preprocessor = UrduTextPreprocessor()
        self.imagery_terms = {
            "love": ["عشق", "محبت", "دل", "یار", "ہجر", "وصال"],
            "sorrow": ["غم", "آنسو", "درد", "تنہائی", "ویرانی"],
            "mystic": ["خدا", "صوفی", "فنا", "بقا", "روح"],
            "nature": ["چاند", "رات", "ہوا", "بارش", "پھول"]
        }

    def normalize(self, text):
        text = self.preprocessor.normalize_urdu(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def tokenize(self, text):
        text = self.normalize(text)
        return text.split()

    def lexical_overlap(self, text_a, text_b):
        tokens_a = set(self.tokenize(text_a))
        tokens_b = set(self.tokenize(text_b))
        if not tokens_a or not tokens_b:
            return 0.0
        overlap = tokens_a.intersection(tokens_b)
        score = len(overlap) / len(tokens_a.union(tokens_b))
        return round(score, 4)

    def sequence_similarity(self, text_a, text_b):
        text_a = self.normalize(text_a)
        text_b = self.normalize(text_b)
        return round(SequenceMatcher(None, text_a, text_b).ratio(), 4)

    def shared_imagery(self, text_a, text_b):
        tokens_a = set(self.tokenize(text_a))
        tokens_b = set(self.tokenize(text_b))
        shared = {}
        for category, words in self.imagery_terms.items():
            words_set = set(words)
            match_a = tokens_a.intersection(words_set)
            match_b = tokens_b.intersection(words_set)
            common = match_a.intersection(match_b)
            if common:
                shared[category] = list(common)
        return shared

    def thematic_resonance(self, text_a, text_b):
        imagery = self.shared_imagery(text_a, text_b)
        categories = len(imagery.keys())
        return round(categories / 4, 4)

    def repeated_phrases(self, text_a, text_b, min_len=2):
        tokens_a = self.tokenize(text_a)
        tokens_b = self.tokenize(text_b)
        phrases = []
        for i in range(len(tokens_a)):
            for j in range(i + min_len, len(tokens_a) + 1):
                phrase = " ".join(tokens_a[i:j])
                if phrase in " ".join(tokens_b):
                    phrases.append(phrase)
        phrases = list(set(phrases))
        phrases = sorted(phrases, key=len, reverse=True)
        return phrases[:10]

    def stylistic_affinity(self, text_a, text_b):
        len_a = len(self.tokenize(text_a))
        len_b = len(self.tokenize(text_b))
        if max(len_a, len_b) == 0:
            return 0.0
        return round(min(len_a, len_b) / max(len_a, len_b), 4)

    def analyze(self, text_a, text_b):
        lexical = self.lexical_overlap(text_a, text_b)
        sequence = self.sequence_similarity(text_a, text_b)
        thematic = self.thematic_resonance(text_a, text_b)
        affinity = self.stylistic_affinity(text_a, text_b)
        repeated = self.repeated_phrases(text_a, text_b)
        imagery = self.shared_imagery(text_a, text_b)
        overall = round((lexical * 0.30 + sequence * 0.30 + thematic * 0.20 + affinity * 0.20), 4)
        return {
            "overall_intertextuality": overall,
            "lexical_overlap": lexical,
            "sequence_similarity": sequence,
            "thematic_resonance": thematic,
            "stylistic_affinity": affinity,
            "shared_imagery": imagery,
            "repeated_phrases": repeated
        }

    def compare_against_corpus(self, input_text, corpus, top_n=5):
        results = []
        for item in corpus:
            analysis = self.analyze(input_text, item["text"])
            results.append({
                "text_id": item["text_id"],
                "poet": item.get("poet"),
                "score": analysis["overall_intertextuality"],
                "analysis": analysis
            })
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_n]


if __name__ == "__main__":
    text1 = "دل میں اک حسرت سی رہ گئی ہے\nکاش وہ ایک بار پھر آ جائیں"
    text2 = "دل کی ویرانی کا کیا مذکور\nیہ نگر سو مرتبہ لوٹا گیا"
    analyzer = IntertextualAnalyzer()
    result = analyzer.analyze(text1, text2)
    print("\nUCPC Intertextual Analysis")
    print("=" * 50)
    for key, value in result.items():
        print(f"{key}:")
        print(value)
        print()