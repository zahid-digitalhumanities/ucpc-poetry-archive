# modules/ai_tools.py
import os

def translate_urdu_to_english(text: str) -> str:
    """Return placeholder to avoid heavy models on Render."""
    if os.environ.get('DISABLE_AI') == '1':
        return "[Translation not available on server]"
    # For local development, you can keep original logic,
    # but ensure you have enough RAM.
    return f"[Translated: {text[:50]}...]"