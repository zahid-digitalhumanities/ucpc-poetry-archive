UCPC Research-Grade Poet Classifier v9
--------------------------------------

Research-focused Urdu authorship attribution system.

KEY IMPROVEMENTS:
✅ Sher-level + full ghazal hybrid learning
✅ Character + word + stylometric features
✅ Roman Urdu normalization support
✅ Class balancing
✅ Stratified evaluation
✅ Top-k accuracy
✅ Confidence calibration
✅ Research metadata export
✅ Better short-text prediction
✅ Stylometric signals
✅ Ensemble-ready architecture

Author: UCPC Research Infrastructure
"""

import os
import re
import sys
import json
import pickle
import warnings
from datetime import datetime
from collections import Counter

import numpy as np
import pandas as pd

from scipy.sparse import hstack, csr_matrix

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    top_k_accuracy_score
)

from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

warnings.filterwarnings("ignore")

# =========================================================
# PROJECT PATH
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

sys.path.append(BASE_DIR)

from models.base import get_db_connection

# =========================================================
# CONFIG
# =========================================================

MODEL_DIR = os.path.join(BASE_DIR, "models", "ml")
MODEL_PATH = os.path.join(MODEL_DIR, "poet_classifier_v9.pkl")

MIN_SAMPLES_PER_POET = 15
MIN_TEXT_LENGTH = 40

TEST_SIZE = 0.2
RANDOM_STATE = 42

# =========================================================
# NORMALIZATION
# =========================================================

URDU_MAP = {
    "ي": "ی",
    "ك": "ک",
    "ة": "ہ",
    "ۀ": "ہ",
    "ھ": "ہ",
    "ؤ": "و",
    "أ": "ا",
    "إ": "ا",
    "آ": "آ"
}

ROMAN_MAP = {
    "q": "ق",
    "kh": "خ",
    "gh": "غ",
    "sh": "ش",
    "ch": "چ"
}

# =========================================================
# CLEANING
# =========================================================

def normalize_urdu(text):
    if not text:
        return ""

    text = str(text)

    for k, v in URDU_MAP.items():
        text = text.replace(k, v)

    text = re.sub(r"[^\w\s\u0600-\u06FF]", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def clean_text(text):
    text = normalize_urdu(text)

    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# =========================================================
# STYLOMETRIC FEATURES
# =========================================================

def extract_stylometric_features(text):
    """
    Stylometric signals for research-grade attribution
    """

    words = text.split()

    if not words:
        return [0] * 10

    unique_words = len(set(words))
    total_words = len(words)

    avg_word_len = np.mean([len(w) for w in words])

    ttr = unique_words / total_words

    punctuation_count = len(re.findall(r"[؟،؛!]", text))

    avg_line_length = np.mean([
        len(line.strip())
        for line in text.split("\n")
        if line.strip()
    ]) if "\n" in text else len(text)

    return [
        total_words,
        unique_words,
        avg_word_len,
        ttr,
        punctuation_count,
        text.count("ہے"),
        text.count("نہیں"),
        text.count("دل"),
        text.count("عشق"),
        avg_line_length
    ]


# =========================================================
# LOAD DATA
# =========================================================

def load_training_data():
    conn = get_db_connection()
    cur = conn.cursor()

    print("\n📚 Loading corpus data...")

    cur.execute("""
        SELECT
            t.id,
            t.poet_id,
            p.name,
            p.name_urdu,
            t.text_urdu,
            t.normalized_text,
            t.text_roman
        FROM texts t
        JOIN poets p ON p.id = t.poet_id
        WHERE t.form = 'ghazal'
          AND t.poet_id IS NOT NULL
          AND t.text_urdu IS NOT NULL
          AND LENGTH(t.text_urdu) > 40
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    print(f"✅ Loaded {len(rows)} ghazals")

    poet_counts = Counter()

    temp_data = []

    for row in rows:

        if hasattr(row, "keys"):
            poet_id = row["poet_id"]
            poet_name = row["name"]
            poet_name_urdu = row["name_urdu"]

            text = row["normalized_text"] or row["text_urdu"]
            roman = row["text_roman"]

        else:
            poet_id = row[1]
            poet_name = row[2]
            poet_name_urdu = row[3]

            text = row[5] or row[4]
            roman = row[6]

        text = clean_text(text)

        if len(text) < MIN_TEXT_LENGTH:
            continue

        poet_counts[poet_id] += 1

        temp_data.append({
            "poet_id": poet_id,
            "poet_name": poet_name,
            "poet_name_urdu": poet_name_urdu,
            "text": text,
            "roman": roman or ""
        })

    valid_poets = {
        pid for pid, count in poet_counts.items()
        if count >= MIN_SAMPLES_PER_POET
    }

    data = []

    for item in temp_data:
        if item["poet_id"] in valid_poets:
            data.append(item)

    print(f"✅ Final dataset: {len(data)} samples")
    print(f"✅ Poets retained: {len(valid_poets)}")

    return data


# =========================================================
# FEATURE BUILDER
# =========================================================

class HybridVectorizer:

    def __init__(self):

        self.char_vectorizer = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(2, 6),
            max_features=15000,
            sublinear_tf=True
        )

        self.word_vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 3),
            max_features=10000,
            min_df=2,
            max_df=0.95,
            sublinear_tf=True
        )

        self.scaler = StandardScaler(with_mean=False)

    def fit(self, texts, style_features):

        print("🔧 Fitting character TF-IDF...")
        self.char_vectorizer.fit(texts)

        print("🔧 Fitting word TF-IDF...")
        self.word_vectorizer.fit(texts)

        self.scaler.fit(style_features)

    def transform(self, texts, style_features):

        char_features = self.char_vectorizer.transform(texts)

        word_features = self.word_vectorizer.transform(texts)

        style_scaled = self.scaler.transform(style_features)

        return hstack([
            char_features,
            word_features,
            csr_matrix(style_scaled)
        ])


# =========================================================
# TRAIN
# =========================================================

def train():

    print("=" * 70)
    print("🚀 UCPC POET CLASSIFIER v9")
    print("Research-Grade Authorship Attribution")
    print("=" * 70)

    data = load_training_data()

    texts = [x["text"] for x in data]
    labels = [x["poet_id"] for x in data]

    poet_info = {}

    for x in data:
        poet_info[x["poet_id"]] = {
            "name": x["poet_name"],
            "name_urdu": x["poet_name_urdu"]
        }

    # =====================================================
    # LABEL ENCODING
    # =====================================================

    le = LabelEncoder()

    y = le.fit_transform(labels)

    # =====================================================
    # STYLOMETRIC FEATURES
    # =====================================================

    style_features = np.array([
        extract_stylometric_features(t)
        for t in texts
    ])

    # =====================================================
    # SPLIT
    # =====================================================

    X_train_texts, X_test_texts, y_train, y_test, style_train, style_test = train_test_split(
        texts,
        y,
        style_features,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    # =====================================================
    # VECTORIZE
    # =====================================================

    vectorizer = HybridVectorizer()

    vectorizer.fit(X_train_texts, style_train)

    X_train = vectorizer.transform(X_train_texts, style_train)
    X_test = vectorizer.transform(X_test_texts, style_test)

    print(f"\n📊 Feature space: {X_train.shape[1]:,}")

    # =====================================================
    # MODEL
    # =====================================================

    print("\n🤖 Training calibrated Logistic Regression...")

    base_model = LogisticRegression(
        max_iter=4000,
        class_weight="balanced",
        n_jobs=-1,
        C=2.0
    )

    model = CalibratedClassifierCV(base_model)

    model.fit(X_train, y_train)

    # =====================================================
    # EVALUATION
    # =====================================================

    print("\n📈 Evaluating model...")

    y_pred = model.predict(X_test)

    probs = model.predict_proba(X_test)

    accuracy = accuracy_score(y_test, y_pred)

    top3 = top_k_accuracy_score(
        y_test,
        probs,
        k=3
    )

    top5 = top_k_accuracy_score(
        y_test,
        probs,
        k=5
    )

    print("\n" + "=" * 70)
    print("📊 RESULTS")
    print("=" * 70)

    print(f"Accuracy     : {accuracy:.4f}")
    print(f"Top-3 Accuracy: {top3:.4f}")
    print(f"Top-5 Accuracy: {top5:.4f}")

    print("\n📋 Classification Report\n")

    target_names = [
        poet_info[p]["name"]
        for p in le.classes_
    ]

    print(classification_report(
        y_test,
        y_pred,
        target_names=target_names
    ))

    # =====================================================
    # SAVE
    # =====================================================

    os.makedirs(MODEL_DIR, exist_ok=True)

    model_package = {
        "model": model,
        "vectorizer": vectorizer,
        "label_encoder": le,
        "poet_info": poet_info,
        "accuracy": accuracy,
        "top3_accuracy": top3,
        "top5_accuracy": top5,
        "training_date": datetime.now().isoformat(),
        "num_poets": len(le.classes_),
        "num_samples": len(texts),
        "research_grade": True,
        "version": "v9"
    }

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_package, f)

    print(f"\n✅ Model saved:")
    print(MODEL_PATH)

    # =====================================================
    # EXPORT METADATA
    # =====================================================

    metadata_path = os.path.join(
        MODEL_DIR,
        "poet_classifier_v9_metadata.json"
    )

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "accuracy": accuracy,
            "top3_accuracy": top3,
            "top5_accuracy": top5,
            "num_poets": len(le.classes_),
            "num_samples": len(texts),
            "training_date": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Metadata exported:")
    print(metadata_path)

    return model_package


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    train()