"""
UCPC Stylometric Validation Engine
Research-grade Digital Humanities stylometry module
"""

import re
import numpy as np
from collections import Counter
from statistics import mean, stdev


class StylometricValidator:
    """
    Extract and compare stylometric signals for Urdu poetry authorship attribution.
    """

    def __init__(self):
        pass

    def normalize_text(self, text):
        if not text:
            return ""
        text = str(text)
        replacements = {"ي": "ی", "ك": "ک", "ة": "ہ", "أ": "ا", "إ": "ا", "آ": "آ"}
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = re.sub(r"[^\u0600-\u06FF\s]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def tokenize(self, text):
        text = self.normalize_text(text)
        return [t for t in text.split() if t.strip()]

    def type_token_ratio(self, text):
        tokens = self.tokenize(text)
        if not tokens:
            return 0
        unique_tokens = len(set(tokens))
        return round(unique_tokens / len(tokens), 4)

    def average_line_length(self, text):
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return 0
        lengths = [len(line.split()) for line in lines]
        return round(mean(lengths), 2)

    def lexical_richness(self, text):
        tokens = self.tokenize(text)
        if not tokens:
            return 0
        frequencies = Counter(tokens)
        hapax = len([w for w, c in frequencies.items() if c == 1])
        return round(hapax / len(tokens), 4)

    def repetition_score(self, text):
        tokens = self.tokenize(text)
        if not tokens:
            return 0
        frequencies = Counter(tokens)
        repeated = sum(count for word, count in frequencies.items() if count > 1)
        return round(repeated / len(tokens), 4)

    def top_words(self, text, top_n=20):
        tokens = self.tokenize(text)
        frequencies = Counter(tokens)
        return frequencies.most_common(top_n)

    def stylometric_profile(self, text):
        profile = {
            "type_token_ratio": self.type_token_ratio(text),
            "average_line_length": self.average_line_length(text),
            "lexical_richness": self.lexical_richness(text),
            "repetition_score": self.repetition_score(text),
            "top_words": self.top_words(text, top_n=15)
        }
        return profile

    def compare_profiles(self, text_a, text_b):
        profile_a = self.stylometric_profile(text_a)
        profile_b = self.stylometric_profile(text_b)
        similarity = {}
        for key in ["type_token_ratio", "average_line_length", "lexical_richness", "repetition_score"]:
            val_a = profile_a[key]
            val_b = profile_b[key]
            diff = abs(val_a - val_b)
            similarity[key] = {
                "text_a": val_a,
                "text_b": val_b,
                "difference": round(diff, 4)
            }
        return {
            "profile_a": profile_a,
            "profile_b": profile_b,
            "comparison": similarity
        }

    def corpus_statistics(self, texts):
        ttr_scores = []
        richness_scores = []
        repetition_scores = []
        for text in texts:
            ttr_scores.append(self.type_token_ratio(text))
            richness_scores.append(self.lexical_richness(text))
            repetition_scores.append(self.repetition_score(text))
        return {
            "documents": len(texts),
            "ttr_mean": round(mean(ttr_scores), 4) if ttr_scores else 0,
            "ttr_std": round(stdev(ttr_scores), 4) if len(ttr_scores) > 1 else 0,
            "richness_mean": round(mean(richness_scores), 4) if richness_scores else 0,
            "repetition_mean": round(mean(repetition_scores), 4) if repetition_scores else 0
        }


if __name__ == "__main__":
    text = """
    دل ہی تو ہے نہ سنگ و خشت
    درد سے بھر نہ آئے کیوں

    روئیں گے ہم ہزار بار
    کوئی ہمیں ستائے کیوں
    """
    validator = StylometricValidator()
    profile = validator.stylometric_profile(text)
    print("\nUCPC Stylometric Profile")
    print("=" * 50)
    for key, value in profile.items():
        print(f"{key}: {value}")