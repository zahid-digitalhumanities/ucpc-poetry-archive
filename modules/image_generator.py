import os
import logging
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

logging.basicConfig(level=logging.INFO)

def reshape_urdu(text):
    if not text:
        return ""
    try:
        return get_display(arabic_reshaper.reshape(text))
    except:
        return text

def get_urdu_font(size):
    # Render's Linux system fonts
    paths = [
        '/usr/share/fonts/truetype/noto/NotoNastaliqUrdu.ttf',
        '/usr/share/fonts/truetype/urdu/NotoNastaliqUrdu-Regular.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def get_poet_font(size):
    paths = [
        '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf',
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except:
                pass
    return ImageFont.load_default()

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width = 600
    top_margin = 80
    bottom_margin = 120
    line_spacing = 50
    verse_spacing = 30
    x_center = width // 2

    urdu_font = get_urdu_font(28)
    poet_font = get_poet_font(24)
    dedication_font = get_poet_font(20)

    # Estimate height
    y = top_margin
    poet_name = ghazal.get('poet_name', '').upper()
    if poet_name:
        y += 45
    for v in verses:
        if v.get('misra1_urdu'):
            y += line_spacing
        if v.get('misra2_urdu'):
            y += line_spacing
        y += verse_spacing
    if dedicator or dedicatee:
        y += 60
    y += bottom_margin
    height = max(y, 800)

    img = Image.new('RGB', (width, height), (15, 35, 60))
    draw = ImageDraw.Draw(img)

    y = top_margin
    if poet_name:
        draw.text((x_center, y), poet_name, font=poet_font, fill=(212, 175, 55), anchor='mt')
        y += 45

    logging.info(f"Drawing {len(verses)} verses")
    for v in verses:
        m1 = reshape_urdu(v.get('misra1_urdu', ''))
        m2 = reshape_urdu(v.get('misra2_urdu', ''))
        if m1:
            draw.text((x_center, y), m1, font=urdu_font, fill=(255, 255, 255), anchor='mt')
            y += line_spacing
        if m2:
            draw.text((x_center, y), m2, font=urdu_font, fill=(255, 255, 255), anchor='mt')
            y += line_spacing
        y += verse_spacing

    if dedicator:
        draw.text((30, height-70), f"from : {dedicator}", font=dedication_font, fill=(212, 175, 55))
    if dedicatee:
        draw.text((30, height-40), f"dedicated to : {dedicatee}", font=dedication_font, fill=(255, 255, 255))

    watermark = "UCPC Archive • Preserving Urdu Poetry"
    draw.text((x_center, height-20), watermark, font=dedication_font, fill=(212, 175, 55, 180), anchor='mb')
    return img
