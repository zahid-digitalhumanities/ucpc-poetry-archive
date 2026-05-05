# UCPC Poetry Archive

A research‑grade digital archive for Urdu poetry with bilingual content, advanced search, voice input, bulk upload, and **AI‑powered analysis** (poet prediction, theme detection, semantic similarity, radif/qaafiya extraction). Built with Flask, PostgreSQL, and deployed on Render.

---

## 🌟 Features

- **Bilingual Display** – Every ghazal/nazm has Urdu and English titles and verses.
- **Advanced Search** – Supports Urdu, Roman Urdu, and English queries with fuzzy matching and autocomplete suggestions.
- **Voice Search** – Use your microphone to speak a query (browser‑based SpeechRecognition).
- **Bulk Upload** – Upload multiple ghazals via text files or paste text; automatic parsing and duplicate detection (content hash based).
- **Contributor Tracking** – Credit users who add ghazals (optional name/email).
- **Book Linking** – Associate ghazals with books by poet.
- **Responsive UI** – Tailwind CSS, custom Urdu font (Jameel Noori Nastaleeq).

### 🤖 AI Research Dashboard (`/research`)

- **Poet Prediction** – ML model (TF‑IDF + XGBoost) predicts the most likely poet from a pasted ghazal, with confidence scores.
- **Theme Detection** – Keyword‑based heuristic identifies dominant themes (Love/Grief, General, etc.).
- **Semantic Similarity** – Find similar ghazals using sentence‑transformer embeddings (multilingual MiniLM).
- **Radif / Qaafiya Extraction** – Rule‑based extraction of rhyme structure (radif = refrain, qaafiya = rhyme words) with confidence.
- **Explainability** – Get a breakdown of why two ghazals are similar (embedding score, radif match, qaafiya overlap, theme match).

### 📥 Unified Ingestion (`/ingest/add`)

- **Single ghazal entry** with poet, source, optional book and contributor.
- **Bulk upload** with `###GHZ###` separator; preview before insertion; duplicate detection via content hash.
- **Automatic NLP** – radif/qaafiya, meter (heuristic), and embedding generation.

---

## 🛠️ Technology Stack

| Layer          | Technology                                      |
|----------------|--------------------------------------------------|
| Backend        | Python 3, Flask                                 |
| Database       | PostgreSQL (Render or local)                    |
| ML / NLP       | XGBoost, scikit‑learn, sentence‑transformers    |
| Frontend       | HTML5, Tailwind CSS, JavaScript                 |
| Search         | PostgreSQL `pg_trgm` (fuzzy) + `ILIKE` + **embedding‑based semantic search** |
| Translation    | `deep-translator` (Google) + fallback dictionary |
| Roman‑Urdu     | Custom mapping engine                           |
| Hosting        | Render                                          |

---

## 🚀 Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/zahid-digitalhumanities/ucpc-poetry-archive.git
cd ucpc-poetry-archive
