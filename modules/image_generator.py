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
    width = 1080
    height = 1920
    bg_color = (10, 10, 20)
    text_color = (255, 255, 255)
    gold = (212, 175, 55)

    poet_font = get_font('LiberationSerif-Bold.ttf', 56)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 44)
    english_font = get_font('LiberationSerif-Regular.ttf', 32)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 38)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Poet name
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    poet_text = f"{poet_ur}\n{poet_en}" if poet_ur else poet_en
    draw.text((width//2, 120), poet_text, font=poet_font, fill=gold, anchor='mt')

    # Verses
    margin = 80
    urdu_x = width - margin
    english_x = margin
    y = 280
    line_spacing = 90
    couplet_spacing = 40

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
        y += couplet_spacing

    # Dedication
    if dedicator and dedicatee:
        y += 80
        draw.text((width//2, y), f"From: {dedicator}", font=dedication_font, fill=gold, anchor='mt')
        y += 60
        draw.text((width//2, y), f"Dedicated to: {dedicatee}", font=dedication_font, fill=text_color, anchor='mt')
        y += 80

    # Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width//2, height - 80), watermark, font=watermark_font, fill=(100,100,100), anchor='mt')
    return img