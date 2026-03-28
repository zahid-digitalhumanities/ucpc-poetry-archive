import os
from gtts import gTTS

AUDIO_FOLDER = "static/audio"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

def generate_audio(text_id, urdu_text, english_text):
    filename = os.path.join(AUDIO_FOLDER, f"{text_id}.mp3")
    if os.path.exists(filename):
        return filename
    full_text = f"{urdu_text}\n{english_text}"
    tts = gTTS(full_text, lang='ur')
    tts.save(filename)
    return filename