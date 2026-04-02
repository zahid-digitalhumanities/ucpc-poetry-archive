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
    Returns a PIL Image with bilingual ghazal layout.
    Urdu on the right, English on the left, side‑by‑side.
    Includes poet name, dedication, watermark.
    """
    width = 1200
    height = 1800  # dynamic height will be adjusted later
    bg_color = (20, 20, 30)
    text_color = (255, 255, 255)
    gold = (212, 175, 55)

    # Fonts
    poet_font = get_font('LiberationSerif-Bold.ttf', 42)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 32)
    english_font = get_font('LiberationSerif-Regular.ttf', 24)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 28)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 20)

    # Calculate required height based on content
    line_spacing = 70
    couplet_spacing = 80
    y = 180

    # Poet name
    poet = ghazal.get('poet_name_urdu', ghazal.get('poet_name', ''))
    y += 50

    # Reserve space for dedication (will be drawn later)
    dedication_height = 0
    if dedicator and dedicatee:
        dedication_height = 140

    # Count lines for verses
    total_lines = 0
    for v in verses:
        if v.get('misra1_urdu'):
            total_lines += 1
        if v.get('misra2_urdu'):
            total_lines += 1
    # Each couplet uses two lines (Urdu + English) actually we draw both columns simultaneously.
    # We'll draw each misra as a separate line in its column.
    # So total lines = number of misras.
    verse_height = total_lines * line_spacing + (len(verses) * 40)
    total_height = y + verse_height + dedication_height + 200
    height = max(total_height, 1800)

    # Create image
    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw poet name (centered)
    draw.text((width//2, 120), poet, font=poet_font, fill=gold, anchor='mt')

    # Draw verses in two columns
    col_width = width // 2
    margin = 60
    urdu_x = width - margin - 20   # right side
    english_x = margin + 20        # left side
    y_start = 220

    y = y_start
    for verse in verses:
        misra1_ur = verse.get('misra1_urdu', '')
        misra2_ur = verse.get('misra2_urdu', '')
        misra1_en = verse.get('misra1_english', '')
        misra2_en = verse.get('misra2_english', '')

        if misra1_ur:
            draw.text((urdu_x, y), misra1_ur, font=urdu_font, fill=text_color, anchor='rt')
            draw.text((english_x, y), misra1_en, font=english_font, fill=text_color, anchor='lt')
            y += line_spacing
        if misra2_ur:
            draw.text((urdu_x, y), misra2_ur, font=urdu_font, fill=text_color, anchor='rt')
            draw.text((english_x, y), misra2_en, font=english_font, fill=text_color, anchor='lt')
            y += line_spacing
        y += couplet_spacing - line_spacing

    # Dedication block
    if dedicator and dedicatee:
        y += 60
        draw.text((width//2, y), f"From: {dedicator}", font=dedication_font, fill=gold, anchor='mt')
        y += 50
        draw.text((width//2, y), f"Dedicated to: {dedicatee}", font=dedication_font, fill=text_color, anchor='mt')
        y += 80

    # Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width//2, height - 40), watermark, font=watermark_font, fill=(150,150,150), anchor='mt')

    return img
