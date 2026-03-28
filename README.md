# UCPC Poetry Archive

A research‑grade digital archive for Urdu poetry with bilingual content, advanced search, voice input, and bulk upload. Built with Flask, PostgreSQL, and deployed on Render.

---

## 🌟 Features

- **Bilingual Display** – Every ghazal/nazm has Urdu and English titles and verses.
- **Advanced Search** – Supports Urdu, Roman Urdu, and English queries with fuzzy matching and autocomplete suggestions.
- **Voice Search** – Use your microphone to speak a query (browser‑based SpeechRecognition).
- **Bulk Upload** – Upload multiple ghazals via text files, ZIP archives, or PDFs; automatic parsing and duplicate detection.
- **Contributor Tracking** – Credit users who add ghazals (optional name/email).
- **Book Linking** – Associate ghazals with books by poet.
- **Responsive UI** – Tailwind CSS, custom Urdu font (Jameel Noori Nastaleeq).

---

## 🛠️ Technology Stack

| Layer       | Technology                          |
|-------------|-------------------------------------|
| Backend     | Python 3, Flask                     |
| Database    | PostgreSQL (Render or local)        |
| Frontend    | HTML5, Tailwind CSS, JavaScript     |
| Search      | PostgreSQL `pg_trgm` (fuzzy) + `ILIKE` |
| Translation | `deep-translator` (Google) + fallback dictionary |
| Roman‑Urdu  | Custom mapping engine               |
| Hosting     | Render                              |

---

## 🚀 Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone https://github.com/zahid-digitalhumanities/ucpc-poetry-archive.git
cd ucpc-poetry-archive
