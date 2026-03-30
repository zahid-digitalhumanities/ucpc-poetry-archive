import os
from elevenlabs import generate, save, set_api_key

# 🔐 Load API key
API_KEY = os.getenv("ELEVENLABS_API_KEY")

if not API_KEY:
    print("❌ ELEVENLABS_API_KEY is NOT set")
else:
    print("✅ ElevenLabs API Key Loaded")

set_api_key(API_KEY)

# 📁 Audio folder
AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def generate_audio(text_id, urdu_text, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}.mp3")

    print("\n" + "="*50)
    print("🎧 GENERATE AUDIO START")
    print(f"TEXT ID: {text_id}")

    # ✅ Use cached file
    if os.path.exists(filename):
        print("⚡ Using cached audio")
        print(f"FILE SIZE: {os.path.getsize(filename)} bytes")
        return filename

    # 📝 Select text
    text = urdu_text if urdu_text else english_text

    if not text:
        print("❌ ERROR: No text available")
        return None

    print(f"TEXT PREVIEW: {text[:100]}")

    try:
        # ✅ FIXED VOICE (multilingual supported)
        audio = generate(
            text=text,
            voice="EXAVITQu4vr4xnSDxMaL",  # 🔥 BEST multilingual voice
            model="eleven_multilingual_v2"
        )

        save(audio, filename)

        # ✅ Verify file
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"✅ AUDIO SAVED: {filename}")
            print(f"📦 FILE SIZE: {size} bytes")

            if size == 0:
                print("❌ ERROR: Empty audio file")
                return None

            return filename
        else:
            print("❌ ERROR: File not created")
            return None

    except Exception as e:
        print("❌ ELEVENLABS ERROR:", str(e))
        return None