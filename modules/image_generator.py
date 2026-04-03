import os
import logging
from PIL import Image, ImageDraw, ImageFont

# Optional Urdu shaping
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

def draw_centered(draw, text, y, font, color, width, spacing=6):
    text = shape_urdu(text)
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + spacing
    return y

def draw_left_aligned(draw, text, y, font, color, left_margin=50):
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((left_margin, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 8

def draw_couplet_on_one_line(draw, misra1, misra2, y, font, color, width, gap=60):
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
    # Facebook‑optimal size (1.91:1 ratio)
    width, height = 1200, 630
    bg = (255, 255, 255)
    black = (0, 0, 0)
    gold = (212, 175, 55)
    gray = (120, 120, 120)

    img = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(img)

    # Gold frame
    frame = 8
    draw.rectangle([frame, frame, width - frame, height - frame], outline=gold, width=frame)

    # Fonts (adjusted for 1200×630)
    poet_ur_font = get_font('JameelNooriNastaleeq.ttf', 38)
    poet_en_font = get_font('LiberationSerif-Bold.ttf', 26)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 28)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 20)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 14)

    y = 30

    # 1. Poet name
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')
    if poet_ur:
        y = draw_centered(draw, poet_ur, y, poet_ur_font, gold, width, 5)
    if poet_en:
        y = draw_centered(draw, poet_en, y, poet_en_font, black, width, 5)

    underline_y = y + 5
    draw.line([(150, underline_y), (width - 150, underline_y)], fill=gold, width=4)
    y += 25

    # 2. First couplet (matla) – find first verse with both misras
    matla_m1, matla_m2 = '', ''
    for verse in verses:
        m1 = verse.get('misra1_urdu', '').strip()
        m2 = verse.get('misra2_urdu', '').strip()
        if m1 and m2:
            matla_m1, matla_m2 = m1, m2
            break

    if matla_m1 and matla_m2:
        try:
            y = draw_couplet_on_one_line(draw, matla_m1, matla_m2, y, urdu_font, black, width, gap=50)
        except Exception:
            # Fallback: draw each misra centered separately
            y = draw_centered(draw, matla_m1, y, urdu_font, black, width)
            y = draw_centered(draw, matla_m2, y, urdu_font, black, width)
    y += 15

    # 3. Dedication section
    if dedicator and dedicatee:
        left_margin = 50
        y = draw_left_aligned(draw, f"From: {dedicator}", y, dedication_font, gold, left_margin)

        ded_line = f"Dedicated to: {dedicatee}"
        bbox = draw.textbbox((0, 0), ded_line, font=dedication_font)
        draw.text((left_margin, y), ded_line, font=dedication_font, fill=black)
        underline_y = y + (bbox[3] - bbox[1]) + 12   # 12px gap
        draw.line(
            [(left_margin, underline_y), (left_margin + (bbox[2] - bbox[0]), underline_y)],
            fill=black,
            width=3
        )
        y += (bbox[3] - bbox[1]) + 20

    # 4. Full ghazal (skip the matla to avoid duplication)
    max_y = height - 60
    for verse in verses:
        m1 = verse.get('misra1_urdu', '').strip()
        m2 = verse.get('misra2_urdu', '').strip()
        # Skip the first couplet (matla) if it matches
        if m1 == matla_m1 and m2 == matla_m2:
            continue
        if y > max_y:
            break
        if m1:
            y = draw_centered(draw, m1, y, urdu_font, black, width, 5)
        if m2:
            y = draw_centered(draw, m2, y, urdu_font, black, width, 5)
        y += 8

    # 5. Watermark
    watermark = "UCPC Poetry Archive"
    draw_centered(draw, watermark, height - 25, watermark_font, gray, width)

    return img
