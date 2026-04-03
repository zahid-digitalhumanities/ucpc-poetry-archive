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

def draw_centered_text(draw, text, y, font, color, width, line_spacing=10):
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (width - line_width) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += bbox[3] - bbox[1] + line_spacing
    return y

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width = 1080
    height = 1920
    bg_color = (255, 255, 255)      # white background
    text_color = (0, 0, 0)          # black text
    gold = (212, 175, 55)           # gold for accents
    dark_gray = (50, 50, 50)

    # Fonts
    dedication_font = get_font('LiberationSerif-Bold.ttf', 44)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    poet_font = get_font('LiberationSerif-Bold.ttf', 58)
    poet_eng_font = get_font('LiberationSerif-BoldItalic.ttf', 42)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Beautiful gold frame
    frame_width = 15
    draw.rectangle([frame_width, frame_width, width - frame_width, height - frame_width],
                   outline=gold, width=frame_width)

    # 2. Dedication section (top)
    y = 140
    if dedicator and dedicatee:
        draw_centered_text(draw, f"From: {dedicator}", y, dedication_font, gold, width)
        y += 80
        draw_centered_text(draw, f"Dedicated to: {dedicatee}", y, dedication_font, gold, width)
        y += 120
    else:
        y = 160

    # 3. First couplet (just the first line? but we'll display full verses later; to avoid duplication, we skip special first couplet)
    # Instead, we'll just start with the full ghazal.
    # But the user wants "mira1_urdu" example? We'll simply display all verses normally.

    # 4. Full ghazal (all couplets)
    for verse in verses:
        misra1 = verse.get('misra1_urdu', '')
        misra2 = verse.get('misra2_urdu', '')
        if misra1:
            draw_centered_text(draw, misra1, y, urdu_font, text_color, width, line_spacing=20)
            y += 90
        if misra2:
            draw_centered_text(draw, misra2, y, urdu_font, text_color, width, line_spacing=20)
            y += 90
        y += 40   # extra space between couplets

    # 5. Poet name (Urdu + English) with underline and bold
    y += 80
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    if poet_ur:
        draw_centered_text(draw, poet_ur, y, poet_font, gold, width)
        y += 80
    if poet_en:
        draw_centered_text(draw, poet_en, y, poet_eng_font, dark_gray, width)
        y += 40
    # Underline below poet name
    underline_y = y - 30
    draw.line([(300, underline_y), (width - 300, underline_y)], fill=gold, width=5)

    # 6. Watermark at bottom
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw_centered_text(draw, watermark, height - 100, watermark_font, (150,150,150), width)

    return img