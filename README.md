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

 Clone the repository

```bash
git clone https://github.com/zahid-digitalhumanities/ucpc-poetry-archive.git
cd ucpc-poetry-archive

python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
pip install -r requirements.txt
Set up the database
Create a PostgreSQL database (e.g., ucpc_v3_db).

Run the SQL schema (see database/schema.sql – not included in this repo; you need to create tables from your own export).

Add environment variables (see .env.example – create a .env file with your DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, and SECRET_KEY).
Run the app
bash
python app.py
Visit http://127.0.0.1:10000 (or the port you set).

 Repository Structure (Public)
This repository contains only code and trained models. The full Urdu ghazal corpus is not included due to copyright and research integrity.
ucpc-poetry-archive/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
├── models/
│   ├── base.py, ghazal_model.py, ingest_pipeline.py, ...
│   ├── ai_engine/
│   │   ├── poet_prediction_ai.py
│   │   └── similarity_model.py
│   └── ml/
│       ├── poet_classifier_v7.pkl
│       └── train_poet_classifier_v7.py
├── modules/
│   ├── embeddings.py
│   ├── radif_qaafiya.py
│   ├── meter.py, theme.py, ai_tools.py, image_generator.py
├── routes/
│   ├── ingest_routes.py
│   ├── ai_routes.py
│   ├── ask_ucpc_index.py
│   └── ...
├── static/
│   ├── css/, js/, fonts/, images/
├── templates/
│   ├── base.html, index.html, view.html
│   ├── ghazal_ingest.html, ask_ucpc.html
│   └── ...
└── scripts/
    ├── export_training_data.py
    ├── train_poet_classifier_v7.py
    └── ... (utility scripts)
    Data Availability
The complete Urdu ghazal corpus (5,800+ texts) is not publicly included in this repository.
The repository contains:

All source code

The trained ML model (poet_classifier_v7.pkl)

Sample frontend assets

Utility scripts

To train or retrain the model, you need your own dataset. The training script train_poet_classifier_v7.py reads from scripts/training_data.csv. You must generate this file from your own corpus (e.g., using export_training_data.py after importing ghazals into the database).

Researchers may request access to the corpus for academic purposes – please contact the author.
Contributing
Contributions are welcome! Please open an issue or pull request.

📧 Contact
Muhammad Zahid – GitHub
Project Link: https://github.com/zahid-digitalhumanities/ucpc-poetry-archive


