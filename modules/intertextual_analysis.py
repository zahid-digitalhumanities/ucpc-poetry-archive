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
from functools import lru_cache


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
        # Cache for tokenized texts (performance optimization)
        self._token_cache = {}

    def normalize(self, text):
        """Normalize Urdu text."""
        if not text:
            return ""
        text = self.preprocessor.normalize_urdu(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def tokenize(self, text):
        """Tokenize text with caching."""
        if not text:
            return []
        
        # Use cache for repeated tokenizations
        text_hash = hash(text)
        if text_hash in self._token_cache:
            return self._token_cache[text_hash]
        
        text = self.normalize(text)
        tokens = text.split()
        
        # Limit cache size to prevent memory issues
        if len(self._token_cache) < 1000:
            self._token_cache[text_hash] = tokens
        
        return tokens

    def lexical_overlap(self, text_a, text_b):
        """Calculate Jaccard similarity between token sets."""
        if not text_a or not text_b:
            return 0.0
        
        tokens_a = set(self.tokenize(text_a))
        tokens_b = set(self.tokenize(text_b))
        
        if not tokens_a or not tokens_b:
            return 0.0
        
        overlap = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        score = len(overlap) / len(union) if union else 0.0
        return round(score, 4)

    def sequence_similarity(self, text_a, text_b):
        """Calculate sequence similarity using difflib."""
        if not text_a or not text_b:
            return 0.0
        
        text_a = self.normalize(text_a)
        text_b = self.normalize(text_b)
        
        if not text_a or not text_b:
            return 0.0
        
        return round(SequenceMatcher(None, text_a, text_b).ratio(), 4)

    def shared_imagery(self, text_a, text_b):
        """Detect shared imagery categories between texts."""
        if not text_a or not text_b:
            return {}
        
        tokens_a = set(self.tokenize(text_a))
        tokens_b = set(self.tokenize(text_b))
        
        if not tokens_a or not tokens_b:
            return {}
        
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
        """Calculate thematic resonance score based on shared imagery."""
        if not text_a or not text_b:
            return 0.0
        
        imagery = self.shared_imagery(text_a, text_b)
        categories = len(imagery.keys())
        score = categories / len(self.imagery_terms) if self.imagery_terms else 0.0
        return round(score, 4)

    def repeated_phrases(self, text_a, text_b, min_len=2):
        """Find repeated phrases between texts."""
        if not text_a or not text_b:
            return []
        
        tokens_a = self.tokenize(text_a)
        tokens_b = self.tokenize(text_b)
        
        if len(tokens_a) < min_len or len(tokens_b) < min_len:
            return []
        
        phrases = []
        text_b_str = " ".join(tokens_b)
        
        for i in range(len(tokens_a)):
            for j in range(i + min_len, min(len(tokens_a), i + 20) + 1):  # Limit phrase length
                phrase = " ".join(tokens_a[i:j])
                if len(phrase) > 50:  # Skip very long phrases
                    continue
                if phrase in text_b_str:
                    phrases.append(phrase)
        
        # Remove duplicates and sort by length (longest first)
        phrases = list(set(phrases))
        phrases = sorted(phrases, key=len, reverse=True)
        
        return phrases[:10]  # Return top 10 longest phrases

    def stylistic_affinity(self, text_a, text_b):
        """Calculate stylistic affinity based on text length ratio."""
        if not text_a or not text_b:
            return 0.0
        
        len_a = len(self.tokenize(text_a))
        len_b = len(self.tokenize(text_b))
        
        if max(len_a, len_b) == 0:
            return 0.0
        
        score = min(len_a, len_b) / max(len_a, len_b)
        return round(score, 4)

    def analyze(self, text_a, text_b):
        """
        Comprehensive intertextual analysis between two texts.
        
        Args:
            text_a (str): First text
            text_b (str): Second text
            
        Returns:
            dict: Complete analysis with all metrics
        """
        # Defensive checks
        if not text_a or not text_b:
            return self._empty_analysis_result()
        
        # Convert to string and handle None
        text_a = str(text_a) if text_a else ""
        text_b = str(text_b) if text_b else ""
        
        # Skip if both texts are empty
        if not text_a.strip() or not text_b.strip():
            return self._empty_analysis_result()
        
        # Calculate all metrics
        lexical = self.lexical_overlap(text_a, text_b)
        sequence = self.sequence_similarity(text_a, text_b)
        thematic = self.thematic_resonance(text_a, text_b)
        affinity = self.stylistic_affinity(text_a, text_b)
        repeated = self.repeated_phrases(text_a, text_b)
        imagery = self.shared_imagery(text_a, text_b)
        
        # Weighted overall score (weights sum to 1.0)
        overall = round(
            (lexical * 0.30 + 
             sequence * 0.30 + 
             thematic * 0.20 + 
             affinity * 0.20), 
            4
        )
        
        return {
            "overall_intertextuality": overall,
            "lexical_overlap": lexical,
            "sequence_similarity": sequence,
            "thematic_resonance": thematic,
            "stylistic_affinity": affinity,
            "shared_imagery": imagery,
            "repeated_phrases": repeated,
            "analysis_metadata": {
                "text_a_length": len(self.tokenize(text_a)),
                "text_b_length": len(self.tokenize(text_b)),
                "version": "2.0"
            }
        }
    
    def _empty_analysis_result(self):
        """Return empty analysis result for invalid inputs."""
        return {
            "overall_intertextuality": 0.0,
            "lexical_overlap": 0.0,
            "sequence_similarity": 0.0,
            "thematic_resonance": 0.0,
            "stylistic_affinity": 0.0,
            "shared_imagery": {},
            "repeated_phrases": [],
            "analysis_metadata": {
                "text_a_length": 0,
                "text_b_length": 0,
                "version": "2.0",
                "error": "Invalid input"
            }
        }

    def compare_against_corpus(self, input_text, corpus, top_n=5):
        """
        Compare input text against a corpus of texts.
        
        Args:
            input_text (str): Query text
            corpus (list): List of dicts with 'text_id', 'text', 'poet' keys
            top_n (int): Number of top results to return
            
        Returns:
            list: Top N most intertextually similar texts
        """
        if not input_text or not corpus:
            return []
        
        results = []
        for item in corpus:
            analysis = self.analyze(input_text, item.get("text", ""))
            results.append({
                "text_id": item.get("text_id"),
                "poet": item.get("poet"),
                "poet_urdu": item.get("poet_urdu", ""),
                "title": item.get("title", ""),
                "score": analysis["overall_intertextuality"],
                "analysis": analysis
            })
        
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_n]
    
    def clear_cache(self):
        """Clear the tokenization cache to free memory."""
        self._token_cache.clear()


# Singleton instance for reuse across the application
_intertextual_analyzer = None

def get_intertextual_analyzer():
    """Get singleton instance of IntertextualAnalyzer."""
    global _intertextual_analyzer
    if _intertextual_analyzer is None:
        _intertextual_analyzer = IntertextualAnalyzer()
    return _intertextual_analyzer


# Quick test
if __name__ == "__main__":
    text1 = "دل میں اک حسرت سی رہ گئی ہے\nکاش وہ ایک بار پھر آ جائیں"
    text2 = "دل کی ویرانی کا کیا مذکور\nیہ نگر سو مرتبہ لوٹا گیا"
    
    analyzer = get_intertextual_analyzer()
    result = analyzer.analyze(text1, text2)
    
    print("\n📖 UCPC Intertextual Analysis")
    print("=" * 60)
    print(f"Overall Intertextuality Score: {result['overall_intertextuality']}")
    print(f"Lexical Overlap: {result['lexical_overlap']}")
    print(f"Sequence Similarity: {result['sequence_similarity']}")
    print(f"Thematic Resonance: {result['thematic_resonance']}")
    print(f"Stylistic Affinity: {result['stylistic_affinity']}")
    print(f"\nShared Imagery: {result['shared_imagery']}")
    print(f"\nRepeated Phrases: {result['repeated_phrases'][:3]}")
    print("=" * 60)
