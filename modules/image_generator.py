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

def draw_centered_text(draw, text, y, font, color, width):
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += bbox[3] - bbox[1] + 10
    return y

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width = 1080
    height = 1920
    bg_color = (10, 10, 20)
    text_color = (255, 255, 255)
    gold = (212, 175, 55)

    # Fonts
    poet_font = get_font('LiberationSerif-Bold.ttf', 60)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    english_font = get_font('LiberationSerif-Regular.ttf', 36)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 42)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 30)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Thick gold border around the whole image
    border_width = 10
    draw.rectangle([border_width, border_width, width - border_width, height - border_width],
                   outline=gold, width=border_width)

    # 2. Poet name (Urdu + English)
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    poet_text = f"{poet_ur}\n{poet_en}" if poet_ur else poet_en
    y = draw_centered_text(draw, poet_text, 140, poet_font, gold, width)

    # 3. Bilingual verses with vertical dashed line
    margin = 100
    urdu_x = width - margin
    english_x = margin
    y = max(y + 60, 300)
    line_spacing = 100
    couplet_spacing = 50

    # Draw vertical dashed line in the middle
    middle_x = width // 2
    dash_height = 20
    dash_gap = 20
    for dash_y in range(y, height - 200, dash_height + dash_gap):
        draw.line((middle_x, dash_y, middle_x, dash_y + dash_height), fill=gold, width=3)

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

    # 4. Dedication block
    if dedicator and dedicatee:
        y += 100
        draw.text((width//2, y), f"From: {dedicator}", font=dedication_font, fill=gold, anchor='mt')
        y += 70
        draw.text((width//2, y), f"Dedicated to: {dedicatee}", font=dedication_font, fill=text_color, anchor='mt')
        y += 100

    # 5. Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width//2, height - 100), watermark, font=watermark_font, fill=(100,100,100), anchor='mt')

    return img