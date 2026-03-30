import os
from elevenlabs import ElevenLabs

# Read the API key from the environment variable (set on Render)
client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

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
