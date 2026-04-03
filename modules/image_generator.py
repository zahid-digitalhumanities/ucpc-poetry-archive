import os
import logging
from PIL import Image, ImageDraw, ImageFont

# Try to import shaping libraries (optional but improves Urdu rendering)
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    SHAPE_URDU = True
except ImportError:
    SHAPE_URDU = False

def shape_urdu(text):
    if SHAPE_URDU and text:
        try:
            reshaped = arabic_reshaper.reshape(text)
            return get_display(reshaped)
        except:
            return text
    return text

FONT_CACHE = {}

def get_font(font_name, size):
    key = (font_name, size)
    if key in FONT_CACHE:
        return FONT_CACHE[key]

    base_dir = os.path.dirname(os.path.dirname(__file__))
    font_path = os.path.join(base_dir, 'static', 'fonts', font_name)

    try:
        font = ImageFont.truetype(font_path, size)
    except Exception as e:
        logging.warning(f"Could not load {font_name}: {e}")
        font = ImageFont.load_default()

    FONT_CACHE[key] = font
    return font

def draw_centered(draw, text, y, font, color, width, spacing=10):
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + spacing
    return y

def draw_left_aligned(draw, text, y, font, color, left_margin=80):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((left_margin, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 10

def draw_couplet_on_one_line(draw, misra1, misra2, y, font, color, width, gap=100):
    """Draw misra1 (right) and misra2 (left) on the same line, centered as a pair."""
    m1 = shape_urdu(misra1)
    m2 = shape_urdu(misra2)

    bbox1 = draw.textbbox((0, 0), m1, font=font)
    bbox2 = draw.textbbox((0, 0), m2, font=font)
    width1 = bbox1[2] - bbox1[0]
    width2 = bbox2[2] - bbox2[0]
    total_width = width1 + gap + width2
    start_x = (width - total_width) // 2

    # misra1 (right side)
    draw.text((start_x + width2 + gap, y), m1, font=font, fill=color, anchor='rt')
    # misra2 (left side)
    draw.text((start_x + width2, y), m2, font=font, fill=color, anchor='lt')

    line_height = max(bbox1[3] - bbox1[1], bbox2[3] - bbox2[1])
    return y + line_height + 30

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width, height = 1080, 1920
    bg = (255, 255, 255)
    black = (0, 0, 0)
    gold = (212, 175, 55)
    gray = (120, 120, 120)

    img = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Gold frame
    frame = 15
    draw.rectangle([frame, frame, width - frame, height - frame], outline=gold, width=frame)

    # Fonts
    poet_ur_font = get_font('JameelNooriNastaleeq.ttf', 60)
    poet_en_font = get_font('LiberationSerif-Bold.ttf', 46)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 44)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    y = 120

    # 1. Poet name (centered, with underline)
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    if poet_ur:
        y = draw_centered(draw, poet_ur, y, poet_ur_font, gold, width, 10)
    if poet_en:
        y = draw_centered(draw, poet_en, y, poet_en_font, black, width, 10)

    underline_y = y + 10
    margin_line = 200
    draw.line([(margin_line, underline_y), (width - margin_line, underline_y)], fill=gold, width=8)
    y += 80

    # 2. First couplet (on one line, centered, misra1 right, misra2 left)
    if verses:
        first = verses[0]
        m1 = first.get('misra1_urdu', '')
        m2 = first.get('misra2_urdu', '')
        if m1 and m2:
            y = draw_couplet_on_one_line(draw, m1, m2, y, urdu_font, black, width, gap=100)
        elif m1:
            y = draw_centered(draw, m1, y, urdu_font, black, width)
        y += 40

    # 3. Dedication section (left‑aligned)
    if dedicator and dedicatee:
        y += 20
        left_margin = 80

        # From
        y = draw_left_aligned(draw, f"From: {dedicator}", y, dedication_font, gold, left_margin)

        # Dedicated to (full line underlined)
        ded_line = f"Dedicated to: {dedicatee}"
        bbox_full = draw.textbbox((0, 0), ded_line, font=dedication_font)
        draw.text((left_margin, y), ded_line, font=dedication_font, fill=black)
        underline_y_name = y + (bbox_full[3] - bbox_full[1]) + 8
        draw.line([(left_margin, underline_y_name), (left_margin + (bbox_full[2] - bbox_full[0]), underline_y_name)], fill=black, width=6)
        y += (bbox_full[3] - bbox_full[1]) + 30

    # 4. Full ghazal (all verses, centered)
    for verse in verses:
        m1 = verse.get('misra1_urdu', '')
        m2 = verse.get('misra2_urdu', '')
        if m1:
            y = draw_centered(draw, m1, y, urdu_font, black, width, 10)
        if m2:
            y = draw_centered(draw, m2, y, urdu_font, black, width, 10)
        y += 20
        if y > height - 250:
            break

    # 5. Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw_centered(draw, watermark, height - 120, watermark_font, gray, width)

    return img