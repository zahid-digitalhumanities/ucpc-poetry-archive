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
    """Draw centered text (supports multiline)."""
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
    bg_color = (10, 10, 20)        # dark background
    text_color = (255, 255, 255)
    gold = (212, 175, 55)
    black = (0, 0, 0)

    # Fonts
    dedication_font = get_font('LiberationSerif-Bold.ttf', 42)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    poet_font = get_font('LiberationSerif-Bold.ttf', 56)
    poet_eng_font = get_font('LiberationSerif-Italic.ttf', 40)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 30)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Thick dark border around the whole image
    border_width = 12
    draw.rectangle([border_width, border_width, width - border_width, height - border_width],
                   outline=black, width=border_width)

    # 2. Dedication section (top)
    y = 120
    if dedicator and dedicatee:
        draw_centered_text(draw, f"From: {dedicator}", y, dedication_font, gold, width)
        y += 70
        draw_centered_text(draw, f"Dedicated to: {dedicatee}", y, dedication_font, text_color, width)
        y += 120
    else:
        y = 150

    # 3. First couplet (example or actual first verse)
    if verses:
        first_couplet = verses[0].get('misra1_urdu', '')
        if first_couplet:
            draw_centered_text(draw, first_couplet, y, urdu_font, text_color, width)
            y += 100
    else:
        y += 100

    # 4. Thick black line
    line_y = y
    draw.line([(100, line_y), (width - 100, line_y)], fill=black, width=8)
    y += 60

    # 5. Poet name (Urdu + English) with underline
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    if poet_ur:
        draw_centered_text(draw, poet_ur, y, poet_font, gold, width)
        y += 70
    if poet_en:
        draw_centered_text(draw, poet_en, y, poet_eng_font, text_color, width)
        y += 50
    # Underline below poet name
    underline_y = y - 20
    draw.line([(200, underline_y), (width - 200, underline_y)], fill=gold, width=4)
    y += 80

    # 6. Full ghazal in Urdu (all verses)
    verse_texts = []
    for verse in verses:
        m1 = verse.get('misra1_urdu', '')
        m2 = verse.get('misra2_urdu', '')
        if m1:
            verse_texts.append(m1)
        if m2:
            verse_texts.append(m2)
        verse_texts.append('')  # spacer between couplets

    for line in verse_texts:
        if line:
            draw_centered_text(draw, line, y, urdu_font, text_color, width, line_spacing=20)
            y += 80
        else:
            y += 50

    # 7. Watermark at bottom
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw_centered_text(draw, watermark, height - 100, watermark_font, (100,100,100), width)

    return img