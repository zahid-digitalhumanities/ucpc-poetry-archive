import os
from elevenlabs.client import ElevenLabs

# API Key (env variable)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

# Audio folder
AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def generate_audio(text_id, urdu_text, english_text):
    """
    Generate AI voice audio for ghazal
    Uses caching (if file exists, reuse)
    """

    filename = os.path.join(AUDIO_FOLDER, f"{text_id}.mp3")

    # ✅ اگر پہلے سے audio موجود ہے تو دوبارہ generate نہ کرو
    if os.path.exists(filename):
        return filename

    # ✅ Urdu + English combine
    full_text = f"{urdu_text}\n\n{english_text}"

    try:
        audio_stream = client.text_to_speech.convert(
            text=full_text,
            voice_id="21m00Tcm4TlvDq8ikWAM",  # 🔥 Female (Rachel)
            model_id="eleven_multilingual_v2"
        )

        # Save audio file
        with open(filename, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        return filename

    except Exception as e:
        print("❌ Audio generation error:", str(e))
        return None