# models/vectorizers.py
"""
Vectorizer classes for poet attribution model
These must match exactly with training
"""

from scipy.sparse import hstack

class HybridVectorizer:
    """Matches the vectorizer used in training v9"""
    
    def __init__(self):
        self.char_vectorizer = None
        self.word_vectorizer = None
        self.fitted = False
    
    def __setstate__(self, state):
        self.__dict__.update(state)
    
    def transform(self, texts):
        if not self.fitted:
            raise ValueError("Vectorizer not fitted.")
        char_features = self.char_vectorizer.transform(texts)
        word_features = self.word_vectorizer.transform(texts)
        return hstack([char_features, word_features])


class AdvancedTextVectorizer:
    """Matches the vectorizer used in training v8"""
    
    def __init__(self):
        self.char_vectorizer = None
        self.word_vectorizer = None
        self.fitted = False
    
    def __setstate__(self, state):
        self.__dict__.update(state)
    
    def transform(self, texts):
        if not self.fitted:
            raise ValueError("Vectorizer not fitted.")
        char_features = self.char_vectorizer.transform(texts)
        word_features = self.word_vectorizer.transform(texts)
        return hstack([char_features, word_features])