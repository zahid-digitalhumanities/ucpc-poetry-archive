import os
import logging
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name, size):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    font_path = os.path.join(base_dir, 'static', 'fonts', font_name)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        logging.warning(f"Could not load {font_name}: {e}")
        return ImageFont.load_default()

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width = 1200
    height = 1800
    bg_color = (20, 20, 30)
    text_color = (255, 255, 255)
    gold = (212, 175, 55)

    # Fonts (fallback if missing)
    poet_font = get_font('LiberationSerif-Bold.ttf', 48)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 38)
    english_font = get_font('LiberationSerif-Regular.ttf', 28)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 32)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 24)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Poet name (centered)
    poet = ghazal.get('poet_name_urdu', ghazal.get('poet_name', ''))
    draw.text((width//2, 120), poet, font=poet_font, fill=gold, anchor='mt')

    # Dedication block (if names provided)
    y = 240
    if dedicator and dedicatee:
        draw.text((width//2, y), f"From: {dedicator}", font=dedication_font, fill=gold, anchor='mt')
        y += 60
        draw.text((width//2, y), f"Dedicated to: {dedicatee}", font=dedication_font, fill=text_color, anchor='mt')
        y += 100
    else:
        y = 220

    # Bilingual verses (Urdu right, English left)
    margin = 80
    urdu_x = width - margin
    english_x = margin
    line_spacing = 90

    for verse in verses:
        m1_ur = verse.get('misra1_urdu', '')
        m2_ur = verse.get('misra2_urdu', '')
        m1_en = verse.get('misra1_english', '')
        m2_en = verse.get('misra2_english', '')

        if m1_ur:
            draw.text((urdu_x, y), m1_ur, font=urdu_font, fill=text_color, anchor='rt')
            draw.text((english_x, y), m1_en, font=english_font, fill=text_color, anchor='lt')
            y += line_spacing
        if m2_ur:
            draw.text((urdu_x, y), m2_ur, font=urdu_font, fill=text_color, anchor='rt')
            draw.text((english_x, y), m2_en, font=english_font, fill=text_color, anchor='lt')
            y += line_spacing
        y += 30  # extra space between couplets

    # Watermark (bottom)
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width//2, height - 60), watermark, font=watermark_font, fill=(150,150,150), anchor='mt')

    return img
