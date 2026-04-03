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

def draw_centered(draw, text, y, font, color, width, spacing=8):
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + spacing
    return y

def draw_left_aligned(draw, text, y, font, color, left_margin=40):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((left_margin, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 10

def draw_couplet_on_one_line(draw, misra1, misra2, y, font, color, width, gap=80):
    m1 = shape_urdu(misra1)
    m2 = shape_urdu(misra2)

    bbox1 = draw.textbbox((0, 0), m1, font=font)
    bbox2 = draw.textbbox((0, 0), m2, font=font)
    width1 = bbox1[2] - bbox1[0]
    width2 = bbox2[2] - bbox2[0]
    total_width = width1 + gap + width2
    start_x = (width - total_width) // 2

    draw.text((start_x + width2 + gap, y), m1, font=font, fill=color, anchor='rt')
    draw.text((start_x + width2, y), m2, font=font, fill=color, anchor='lt')

    line_height = max(bbox1[3] - bbox1[1], bbox2[3] - bbox2[1])
    return y + line_height + 20

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width, height = 1200, 630   # Facebook recommended size
    bg = (255, 255, 255)
    black = (0, 0, 0)
    gold = (212, 175, 55)
    gray = (120, 120, 120)

    img = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Gold frame
    frame = 8
    draw.rectangle([frame, frame, width - frame, height - frame], outline=gold, width=frame)

    # Fonts (smaller for this aspect ratio)
    poet_ur_font = get_font('JameelNooriNastaleeq.ttf', 36)
    poet_en_font = get_font('LiberationSerif-Bold.ttf', 28)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 28)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 24)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 16)

    y = 30

    # 1. Poet name
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    if poet_ur:
        y = draw_centered(draw, poet_ur, y, poet_ur_font, gold, width, 6)
    if poet_en:
        y = draw_centered(draw, poet_en, y, poet_en_font, black, width, 6)

    underline_y = y + 5
    margin_line = 150
    draw.line([(margin_line, underline_y), (width - margin_line, underline_y)], fill=gold, width=6)
    y += 25

    # 2. First couplet (on one line)
    if verses:
        first = verses[0]
        m1 = first.get('misra1_urdu', '')
        m2 = first.get('misra2_urdu', '')
        if m1 and m2:
            y = draw_couplet_on_one_line(draw, m1, m2, y, urdu_font, black, width, gap=60)
        elif m1:
            y = draw_centered(draw, m1, y, urdu_font, black, width)
        y += 15

    # 3. Dedication
    if dedicator and dedicatee:
        left_margin = 40
        y += 10
        y = draw_left_aligned(draw, f"From: {dedicator}", y, dedication_font, gold, left_margin)

        ded_line = f"Dedicated to: {dedicatee}"
        bbox_full = draw.textbbox((0, 0), ded_line, font=dedication_font)
        draw.text((left_margin, y), ded_line, font=dedication_font, fill=black)
        underline_y_name = y + (bbox_full[3] - bbox_full[1]) + 8
        draw.line([(left_margin, underline_y_name), (left_margin + (bbox_full[2] - bbox_full[0]), underline_y_name)], fill=black, width=4)
        y += (bbox_full[3] - bbox_full[1]) + 15

    # 4. Full ghazal (centered, but limited space)
    # Only show first few couplets to fit in 630px height
    max_y = height - 50
    for verse in verses:
        if y > max_y:
            break
        m1 = verse.get('misra1_urdu', '')
        m2 = verse.get('misra2_urdu', '')
        if m1:
            y = draw_centered(draw, m1, y, urdu_font, black, width, 6)
        if m2:
            y = draw_centered(draw, m2, y, urdu_font, black, width, 6)
        y += 12

    # 5. Watermark
    watermark = "UCPC Poetry Archive"
    draw_centered(draw, watermark, height - 20, watermark_font, gray, width)

    return img
