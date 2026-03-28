import os
from elevenlabs import generate, save, set_api_key

set_api_key(os.getenv("ELEVENLABS_API_KEY"))

AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def generate_audio(text_id, urdu_text, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}.mp3")
    if os.path.exists(filename):
        return filename
    full_text = f"{urdu_text}\n\n{english_text}"
    audio = generate(text=full_text, voice="Rachel", model="eleven_multilingual_v2")
    save(audio, filename)
    return filename