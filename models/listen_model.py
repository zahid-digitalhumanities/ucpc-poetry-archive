import os
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key="sk_7cfc32b51a15329727cacd1c99ebbe1d249015d6962371bd")

AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def generate_audio(text_id, urdu_text, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}.mp3")
    if os.path.exists(filename):
        return filename

    full_text = f"{urdu_text}\n\n{english_text}"
    audio = client.generate(
        text=full_text,
        voice="Rachel",
        model="eleven_multilingual_v2"
    )
    with open(filename, "wb") as f:
        for chunk in audio:
            f.write(chunk)
    return filename