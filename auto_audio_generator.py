<<<<<<< HEAD
import os
import time
import logging
from TTS.api import TTS
from models.ghazal_model import get_all_ghazals

# ========== CONFIGURATION ==========
BATCH_LIMIT = 50       # Number of new ghazals to process per cycle
SLEEP_TIME = 300       # Seconds to sleep between cycles (300 = 5 min)
AUDIO_FOLDER = "static/audio"
LOG_FILE = "audio_generator.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
# ===================================

# Ensure audio folder exists
os.makedirs(AUDIO_FOLDER, exist_ok=True)

logging.info("🔄 Loading TTS model...")
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")


def file_valid(filepath):
    """Return True if file exists and is larger than 1KB (not corrupt/empty)."""
    return os.path.exists(filepath) and os.path.getsize(filepath) > 1000


def generate_audio(text_id, urdu_text, english_text):
    """
    Generate English and/or Urdu audio files for a given ghazal.
    Returns True if at least one file was created.
    """
    created = False

    en_file = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
    ur_file = os.path.join(AUDIO_FOLDER, f"{text_id}_ur.mp3")

    # English audio
    if english_text and not file_valid(en_file):
        try:
            logging.info(f"🎧 Generating EN audio for {text_id}")
            tts.tts_to_file(text=english_text[:1500], file_path=en_file)
            created = True
        except Exception as e:
            logging.error(f"❌ EN Error {text_id}: {e}")

    # Urdu audio
    if urdu_text and not file_valid(ur_file):
        try:
            logging.info(f"🎧 Generating UR audio for {text_id}")
            tts.tts_to_file(text=urdu_text[:1500], file_path=ur_file)
            created = True
        except Exception as e:
            logging.error(f"❌ UR Error {text_id}: {e}")

    return created


def run_batch():
    """Process one batch of ghazals (up to BATCH_LIMIT new ones)."""
    ghazals = get_all_ghazals()
    created_count = 0
    skipped = 0

    for g in ghazals:
        if created_count >= BATCH_LIMIT:
            break

        text_id = g["id"]
        urdu_text = g.get("text_urdu", "")
        english_text = g.get("text_english", "")

        en_file = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
        ur_file = os.path.join(AUDIO_FOLDER, f"{text_id}_ur.mp3")

        # Skip if both files already exist and are valid
        if file_valid(en_file) and file_valid(ur_file):
            skipped += 1
            continue

        result = generate_audio(text_id, urdu_text, english_text)
        if result:
            created_count += 1
            logging.info(f"✅ Progress: {created_count}/{BATCH_LIMIT}")

    return created_count, skipped


def main():
    logging.info("🚀 AUTO AUDIO GENERATOR STARTED")
    cycle = 1

    while True:
        logging.info(f"\n🔁 Cycle #{cycle} started...")
        created, skipped = run_batch()

        logging.info("\n📊 Cycle Summary:")
        logging.info(f"   Created: {created}")
        logging.info(f"   Skipped: {skipped}")

        # Stop if nothing new was generated
        if created == 0:
            logging.info("🎯 ALL AUDIO GENERATED — SYSTEM STOPPING ✅")
            break

        logging.info(f"\n⏳ Sleeping for {SLEEP_TIME // 60} minutes...\n")
        time.sleep(SLEEP_TIME)
        cycle += 1


if __name__ == "__main__":
=======
import os
import time
import logging
from TTS.api import TTS
from models.ghazal_model import get_all_ghazals

# ========== CONFIGURATION ==========
BATCH_LIMIT = 50       # Number of new ghazals to process per cycle
SLEEP_TIME = 300       # Seconds to sleep between cycles (300 = 5 min)
AUDIO_FOLDER = "static/audio"
LOG_FILE = "audio_generator.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
# ===================================

# Ensure audio folder exists
os.makedirs(AUDIO_FOLDER, exist_ok=True)

logging.info("🔄 Loading TTS model...")
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")


def file_valid(filepath):
    """Return True if file exists and is larger than 1KB (not corrupt/empty)."""
    return os.path.exists(filepath) and os.path.getsize(filepath) > 1000


def generate_audio(text_id, urdu_text, english_text):
    """
    Generate English and/or Urdu audio files for a given ghazal.
    Returns True if at least one file was created.
    """
    created = False

    en_file = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
    ur_file = os.path.join(AUDIO_FOLDER, f"{text_id}_ur.mp3")

    # English audio
    if english_text and not file_valid(en_file):
        try:
            logging.info(f"🎧 Generating EN audio for {text_id}")
            tts.tts_to_file(text=english_text[:1500], file_path=en_file)
            created = True
        except Exception as e:
            logging.error(f"❌ EN Error {text_id}: {e}")

    # Urdu audio
    if urdu_text and not file_valid(ur_file):
        try:
            logging.info(f"🎧 Generating UR audio for {text_id}")
            tts.tts_to_file(text=urdu_text[:1500], file_path=ur_file)
            created = True
        except Exception as e:
            logging.error(f"❌ UR Error {text_id}: {e}")

    return created


def run_batch():
    """Process one batch of ghazals (up to BATCH_LIMIT new ones)."""
    ghazals = get_all_ghazals()
    created_count = 0
    skipped = 0

    for g in ghazals:
        if created_count >= BATCH_LIMIT:
            break

        text_id = g["id"]
        urdu_text = g.get("text_urdu", "")
        english_text = g.get("text_english", "")

        en_file = os.path.join(AUDIO_FOLDER, f"{text_id}_en.mp3")
        ur_file = os.path.join(AUDIO_FOLDER, f"{text_id}_ur.mp3")

        # Skip if both files already exist and are valid
        if file_valid(en_file) and file_valid(ur_file):
            skipped += 1
            continue

        result = generate_audio(text_id, urdu_text, english_text)
        if result:
            created_count += 1
            logging.info(f"✅ Progress: {created_count}/{BATCH_LIMIT}")

    return created_count, skipped


def main():
    logging.info("🚀 AUTO AUDIO GENERATOR STARTED")
    cycle = 1

    while True:
        logging.info(f"\n🔁 Cycle #{cycle} started...")
        created, skipped = run_batch()

        logging.info("\n📊 Cycle Summary:")
        logging.info(f"   Created: {created}")
        logging.info(f"   Skipped: {skipped}")

        # Stop if nothing new was generated
        if created == 0:
            logging.info("🎯 ALL AUDIO GENERATED — SYSTEM STOPPING ✅")
            break

        logging.info(f"\n⏳ Sleeping for {SLEEP_TIME // 60} minutes...\n")
        time.sleep(SLEEP_TIME)
        cycle += 1


if __name__ == "__main__":
>>>>>>> a881c909ad9bd51fcab3855c8cea05c524f253d2
    main()