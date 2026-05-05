import os
from elevenlabs import generate, save, set_api_key

set_api_key(os.getenv("ELEVENLABS_API_KEY"))

AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def generate_audio(text_id, urdu_text, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}.mp3")

    # ✅ 1. Return cached audio instantly
    if os.path.exists(filename):
        print("⚡ Using cached audio:", filename)
        return filename

    # 📝 Prepare text
    text = urdu_text if urdu_text else english_text

    if not text:
        print("❌ No text found")
        return None

    # 🔥 LIMIT TEXT (VERY IMPORTANT)
    text = text[:2000]

    try:
        print("⏳ Generating audio...")

        audio = generate(
            text=text,
            voice="EXAVITQu4vr4xnSDxMaL",
            model="eleven_multilingual_v2"
        )

        save(audio, filename)

        print("✅ Saved:", filename)
        return filename

    except Exception as e:
        print("❌ ElevenLabs Error:", e)
        return None