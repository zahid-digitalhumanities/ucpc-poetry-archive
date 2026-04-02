import os
import logging
from PIL import Image, ImageDraw, ImageFont

def get_font(font_name, size):
    base_dir = os.path.dirname(os.path.dirname(__file__))
    font_path = os.path.join(base_dir, 'static', 'fonts', font_name)
    try:
        return ImageFont.truetype(font_path, size)
    except:
        return ImageFont.load_default()

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width = 1200
    height = 1800
    bg_color = (20, 20, 30)
    text_color = (255, 255, 255)
    gold = (212, 175, 55)

    # Fonts (fallback to default if missing)
    poet_font = get_font('LiberationSerif-Bold.ttf', 42)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 32)
    english_font = get_font('LiberationSerif-Regular.ttf', 24)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 28)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 20)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Poet name (centered)
    poet = ghazal.get('poet_name_urdu', ghazal.get('poet_name', ''))
    draw.text((width//2, 120), poet, font=poet_font, fill=gold, anchor='mt')

    # Verses: bilingual side‑by‑side
    margin = 60
    urdu_x = width - margin - 20
    english_x = margin + 20
    y = 220
    line_spacing = 70
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
        y += 20

    # Dedication
    if dedicator and dedicatee:
        y += 60
        draw.text((width//2, y), f"From: {dedicator}", font=dedication_font, fill=gold, anchor='mt')
        y += 50
        draw.text((width//2, y), f"Dedicated to: {dedicatee}", font=dedication_font, fill=text_color, anchor='mt')
        y += 80

    # Watermark (must be visible)
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width//2, height - 40), watermark, font=watermark_font, fill=(150,150,150), anchor='mt')

    return img