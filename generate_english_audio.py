<<<<<<< HEAD
import os
from gtts import gTTS
from models.ghazal_model import get_all_ghazals

AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def generate_english_audio(text_id, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
    if os.path.exists(filename):
        return filename

    if not english_text:
        print(f"⚠️ ID {text_id}: No English text, skipping.")
        return None

    print(f"🎧 Generating English audio for ID {text_id}...")
    tts = gTTS(english_text, lang='en')   # English language code
    tts.save(filename)
    print(f"✅ Saved: {filename}")
    return filename

def main():
    print("🚀 Starting English audio generation...\n")
    ghazals = get_all_ghazals()
    total = len(ghazals)
    created = 0
    skipped = 0

    for g in ghazals:
        text_id = g["id"]
        english_text = g.get("text_english", "")

        filename = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
        if os.path.exists(filename):
            print(f"⚡ Already exists: {text_id}_en.mp3 — skipping")
            skipped += 1
            continue

        result = generate_english_audio(text_id, english_text)
        if result:
            created += 1
        else:
            print(f"❌ Failed for ID {text_id}\n")

    print("\n🎯 DONE")
    print(f"Total Ghazals: {total}")
    print(f"Created: {created}")
    print(f"Skipped (cached): {skipped}")

if __name__ == "__main__":
=======
import os
from gtts import gTTS
from models.ghazal_model import get_all_ghazals

AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def generate_english_audio(text_id, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
    if os.path.exists(filename):
        return filename

    if not english_text:
        print(f"⚠️ ID {text_id}: No English text, skipping.")
        return None

    print(f"🎧 Generating English audio for ID {text_id}...")
    tts = gTTS(english_text, lang='en')   # English language code
    tts.save(filename)
    print(f"✅ Saved: {filename}")
    return filename

def main():
    print("🚀 Starting English audio generation...\n")
    ghazals = get_all_ghazals()
    total = len(ghazals)
    created = 0
    skipped = 0

    for g in ghazals:
        text_id = g["id"]
        english_text = g.get("text_english", "")

        filename = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
        if os.path.exists(filename):
            print(f"⚡ Already exists: {text_id}_en.mp3 — skipping")
            skipped += 1
            continue

        result = generate_english_audio(text_id, english_text)
        if result:
            created += 1
        else:
            print(f"❌ Failed for ID {text_id}\n")

    print("\n🎯 DONE")
    print(f"Total Ghazals: {total}")
    print(f"Created: {created}")
    print(f"Skipped (cached): {skipped}")

if __name__ == "__main__":
>>>>>>> a881c909ad9bd51fcab3855c8cea05c524f253d2
    main()