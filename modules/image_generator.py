import os
import logging
from PIL import Image, ImageDraw, ImageFont

# ---------------- FONT CACHE ----------------
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
    """Draw text centered horizontally, multiline support."""
    lines = text.split('\n')
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (width - w) // 2
        draw.text((x, y), line, font=font, fill=color)
        y += (bbox[3] - bbox[1]) + spacing
    return y

def draw_couplet(draw, misra1, misra2, y, font, color, width, gap=100):
    """Draw a couplet with both misras on the same line, centered horizontally."""
    bbox1 = draw.textbbox((0, 0), misra1, font=font)
    bbox2 = draw.textbbox((0, 0), misra2, font=font)
    width1 = bbox1[2] - bbox1[0]
    width2 = bbox2[2] - bbox2[0]
    total_width = width1 + gap + width2
    start_x = (width - total_width) // 2
    # misra1 (right side)
    draw.text((start_x + width2 + gap, y), misra1, font=font, fill=color, anchor='rt')
    # misra2 (left side)
    draw.text((start_x + width2, y), misra2, font=font, fill=color, anchor='lt')
    # Return the maximum height of the two lines
    line_height = max(bbox1[3] - bbox1[1], bbox2[3] - bbox2[1])
    return y + line_height + 20  # extra spacing between couplets

def draw_left_aligned(draw, text, y, font, color, left_margin=80):
    """Draw text left‑aligned."""
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((left_margin, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 10


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
    draw.rectangle([frame, frame, width - frame, height - frame],
                   outline=gold, width=frame)

    # -------- FONTS --------
    poet_ur_font = get_font('JameelNooriNastaleeq.ttf', 60)
    poet_en_font = get_font('LiberationSerif-Bold.ttf', 46)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 44)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    y = 120

    # =========================================================
    # 1. POET NAME (CENTERED + UNDERLINE)
    # =========================================================
    poet_ur = ghazal.get('poet_name_urdu', '')
    poet_en = ghazal.get('poet_name', '')

    if poet_ur:
        y = draw_centered(draw, poet_ur, y, poet_ur_font, gold, width, 10)
    if poet_en:
        y = draw_centered(draw, poet_en, y, poet_en_font, black, width, 10)

    # Underline placed 20 pixels below the last line of poet name
    underline_y = y + 10
    margin_line = 200
    draw.line([(margin_line, underline_y), (width - margin_line, underline_y)],
              fill=gold, width=8)
    y += 80

    # =========================================================
    # 2. ALL COUPLETS (same line, centered, with spacing)
    # =========================================================
    for verse in verses:
        m1 = verse.get('misra1_urdu', '')
        m2 = verse.get('misra2_urdu', '')
        if m1 and m2:
            y = draw_couplet(draw, m1, m2, y, urdu_font, black, width, gap=100)
        elif m1:
            bbox = draw.textbbox((0, 0), m1, font=urdu_font)
            draw.text((width//2, y), m1, font=urdu_font, fill=black, anchor='mt')
            y += bbox[3] - bbox[1] + 30
        # safety: stop if we run out of space
        if y > height - 350:
            break

    # =========================================================
    # 3. DEDICATION (LEFT‑ALIGNED, UNDERLINE ONLY UNDER NAME)
    # =========================================================
    if dedicator and dedicatee:
        y += 40
        left_margin = 80

        # "From: ..."
        y = draw_left_aligned(draw, f"From: {dedicator}", y, dedication_font, gold, left_margin)

        # "Dedicated to: ..."
        prefix = "Dedicated to: "
        full_text = prefix + dedicatee
        draw_left_aligned(draw, full_text, y, dedication_font, black, left_margin)

        # Calculate underline position only under the recipient's name
        prefix_bbox = draw.textbbox((0, 0), prefix, font=dedication_font)
        name_bbox = draw.textbbox((0, 0), dedicatee, font=dedication_font)
        name_start_x = left_margin + (prefix_bbox[2] - prefix_bbox[0])
        name_end_x = name_start_x + (name_bbox[2] - name_bbox[0])
        text_height = name_bbox[3] - name_bbox[1]
        underline_y = y + text_height + 12   # 12 pixels below the text
        draw.line([(name_start_x, underline_y), (name_end_x, underline_y)],
                  fill=black, width=6)

        y += text_height + 60

    # =========================================================
    # 4. WATERMARK
    # =========================================================
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw_centered(draw, watermark, height - 120, watermark_font, gray, width)

    return img