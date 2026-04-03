import os
import logging
from PIL import Image, ImageDraw, ImageFont

# ---------------- FONT LOADER ----------------
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


# ---------------- TEXT HELPERS ----------------

def draw_centered(draw, text, y, font, color, width, spacing=10):
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + spacing
    return y


def draw_right(draw, text, y, font, color, width, margin):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = width - margin - w
    draw.text((x, y), text, font=font, fill=color)
    return bbox


def draw_left(draw, text, y, font, color, margin):
    draw.text((margin, y), text, font=font, fill=color)


# ---------------- MAIN FUNCTION ----------------

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):

    width, height = 1080, 1920

    bg = (255, 255, 255)
    black = (0, 0, 0)
    gold = (212, 175, 55)
    gray = (120, 120, 120)

    img = Image.new('RGB', (width, height), bg)
    draw = ImageDraw.Draw(img)

    # -------- FRAME --------
    frame = 15
    draw.rectangle(
        [frame, frame, width - frame, height - frame],
        outline=gold,
        width=frame
    )

    # -------- FONTS --------
    poet_ur_font = get_font('JameelNooriNastaleeq.ttf', 60)
    poet_en_font = get_font('LiberationSerif-Bold.ttf', 46)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 44)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    # -------- START Y --------
    y = 120

    # =========================================================
    # 1. POET NAME (CENTERED + UNDERLINE FIXED)
    # =========================================================

    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')

    if poet_ur:
        y = draw_centered(draw, poet_ur, y, poet_ur_font, gold, width, 10)

    if poet_en:
        y = draw_centered(draw, poet_en, y, poet_en_font, black, width, 10)

    # underline BELOW (proper spacing)
    underline_y = y + 10
    margin_line = 200
    draw.line(
        [(margin_line, underline_y), (width - margin_line, underline_y)],
        fill=gold,
        width=8
    )

    y += 80

    # =========================================================
    # 2. COUPLETS (RIGHT + LEFT SAME LINE)
    # =========================================================

    margin = 80
    couplet_gap = 70

    for verse in verses:

        m1 = verse.get('misra1_urdu', '')
        m2 = verse.get('misra2_urdu', '')

        if not (m1 or m2):
            continue

        # measure heights
        bbox1 = draw.textbbox((0, 0), m1, font=urdu_font) if m1 else (0,0,0,0)
        bbox2 = draw.textbbox((0, 0), m2, font=urdu_font) if m2 else (0,0,0,0)

        h1 = bbox1[3] - bbox1[1]
        h2 = bbox2[3] - bbox2[1]

        line_height = max(h1, h2)

        # RIGHT (misra1)
        if m1:
            draw_right(draw, m1, y, urdu_font, black, width, margin)

        # LEFT (misra2)
        if m2:
            draw_left(draw, m2, y, urdu_font, black, margin)

        y += line_height + couplet_gap

        # overflow protection
        if y > height - 300:
            break

    # =========================================================
    # 3. DEDICATION (FIXED UNDERLINE BUG 🔥)
    # =========================================================

    if dedicator and dedicatee:

        y += 40
        left_margin = 80

        # FROM
        draw_left(draw, f"From: {dedicator}", y, dedication_font, gold, left_margin)

        bbox_from = draw.textbbox((0, 0), f"From: {dedicator}", font=dedication_font)
        y += (bbox_from[3] - bbox_from[1]) + 20

        # DEDICATED TO
        prefix = "Dedicated to: "
        full_text = prefix + dedicatee

        draw_left(draw, full_text, y, dedication_font, black, left_margin)

        # calculate underline ONLY for name
        prefix_bbox = draw.textbbox((0, 0), prefix, font=dedication_font)
        name_bbox = draw.textbbox((0, 0), dedicatee, font=dedication_font)

        name_start_x = left_margin + (prefix_bbox[2] - prefix_bbox[0])
        name_end_x = name_start_x + (name_bbox[2] - name_bbox[0])

        text_height = name_bbox[3] - name_bbox[1]

        # 🔥 FIXED POSITION (below text, not cutting)
        underline_y = y + text_height + 8

        draw.line(
            [(name_start_x, underline_y), (name_end_x, underline_y)],
            fill=black,
            width=5
        )

        y += text_height + 50

    # =========================================================
    # 4. WATERMARK
    # =========================================================

    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"

    draw_centered(
        draw,
        watermark,
        height - 120,
        watermark_font,
        gray,
        width
    )

    return img