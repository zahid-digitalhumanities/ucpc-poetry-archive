import os
import logging
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name, size):
    """Load font from static/fonts, fallback to default."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    font_path = os.path.join(base_dir, 'static', 'fonts', font_name)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        logging.warning(f"Could not load {font_name}: {e}")
        return ImageFont.load_default()

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    """
    Returns a PIL Image object with the ghazal card.
    """
    width = 1080
    height = 1920
    bg_color = (20, 20, 30)
    text_color = (255, 255, 255)
    gold = (212, 175, 55)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = get_font('LiberationSerif-Bold.ttf', 44)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    poet_font = get_font('LiberationSerif-Italic.ttf', 36)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 32)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 24)

    y = 180
    margin = 80

    # English title
    title_en = ghazal.get('title_english', 'Untitled')
    draw.text((width//2, y), title_en, font=title_font, fill=gold, anchor='mt')
    y += 90

    # Urdu title
    title_ur = ghazal.get('title_urdu', '')
    if title_ur:
        # Urdu text – we assume the font supports Urdu
        draw.text((width//2, y), title_ur, font=urdu_font, fill=text_color, anchor='mt')
        y += 100

    # Poet name
    poet = ghazal.get('poet_name', '')
    draw.text((width//2, y), poet, font=poet_font, fill=gold, anchor='mt')
    y += 130

    # Verses (Urdu only)
    verse_texts = []
    for v in verses:
        misra1 = v.get('misra1_urdu', '')
        misra2 = v.get('misra2_urdu', '')
        if misra1:
            verse_texts.append(misra1)
        if misra2:
            verse_texts.append(misra2)
        verse_texts.append('')  # spacer between couplets

    line_spacing = 80
    for line in verse_texts:
        if line:
            draw.text((width//2, y), line, font=urdu_font, fill=text_color, anchor='mt')
            y += line_spacing
        else:
            y += 50

    # Dedication block
    if dedicator and dedicatee:
        y += 80
        draw.text((width//2, y), f"Shared by: {dedicator}", font=dedication_font, fill=gold, anchor='mt')
        y += 60
        draw.text((width//2, y), f"Dedicated to: {dedicatee}", font=dedication_font, fill=text_color, anchor='mt')
        y += 80

    # Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width//2, height - 60), watermark, font=watermark_font, fill=(150,150,150), anchor='mt')

    return img
