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
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 10

def draw_left_aligned_text(draw, text, y, font, color, left_margin):
    bbox = draw.textbbox((0, 0), text, font=font)
    x = left_margin
    draw.text((x, y), text, font=font, fill=color)
    return y + (bbox[3] - bbox[1]) + 10

def draw_couplet_horizontal(draw, misra1, misra2, y, font, color, width, gap=80):
    """Draw a couplet with both misras on the same line, centered."""
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
    return y + max(bbox1[3] - bbox1[1], bbox2[3] - bbox2[1]) + 20

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):
    width = 1080
    height = 1920
    bg_color = (255, 255, 255)
    text_color = (0, 0, 0)
    gold = (212, 175, 55)
    dark_gray = (50, 50, 50)

    # Fonts
    poet_name_font = get_font('LiberationSerif-Bold.ttf', 56)
    poet_eng_font = get_font('LiberationSerif-BoldItalic.ttf', 44)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 44)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Gold frame
    frame_width = 15
    draw.rectangle([frame_width, frame_width, width - frame_width, height - frame_width],
                   outline=gold, width=frame_width)

    y = 140

    # 1. Poet name – centered
    poet_ur = ghazal.get('name_urdu', '').upper()   # using name_urdu column
    poet_en = ghazal.get('name', '').upper()
    if poet_ur:
        y = draw_centered_text(draw, poet_ur, y, poet_name_font, gold, width)
    if poet_en:
        y = draw_centered_text(draw, poet_en, y, poet_eng_font, dark_gray, width)
    # Underline – 30px below last line
    underline_y = y - 20
    draw.line([(200, underline_y), (width - 200, underline_y)], fill=gold, width=10)
    y += 50

    # 2. All couplets (horizontal, same line for each couplet)
    for verse in verses:
        misra1 = verse.get('misra1_urdu', '')
        misra2 = verse.get('misra2_urdu', '')
        if misra1 and misra2:
            y = draw_couplet_horizontal(draw, misra1, misra2, y, urdu_font, text_color, width, gap=100)
        elif misra1:
            bbox = draw.textbbox((0, 0), misra1, font=urdu_font)
            draw.text((width//2, y), misra1, font=urdu_font, fill=text_color, anchor='mt')
            y += bbox[3] - bbox[1] + 30
        y += 40  # extra space between couplets

    y += 60  # space before dedication

    # 3. Dedication section – left‑aligned
    left_margin = 80
    if dedicator and dedicatee:
        y = draw_left_aligned_text(draw, f"From: {dedicator}", y, dedication_font, gold, left_margin)
        # "Dedicated to: ..."
        ded_text = f"Dedicated to: {dedicatee}"
        # Draw the text
        bbox_full = draw.textbbox((0, 0), ded_text, font=dedication_font)
        x_start = left_margin
        draw.text((x_start, y), ded_text, font=dedication_font, fill=text_color)
        # Underline only the recipient's name – below the text
        prefix = "Dedicated to: "
        prefix_bbox = draw.textbbox((0, 0), prefix, font=dedication_font)
        name_bbox = draw.textbbox((0, 0), dedicatee, font=dedication_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_start_x = x_start + (prefix_bbox[2] - prefix_bbox[0])
        name_end_x = name_start_x + name_width
        underline_y_name = y + 15   # 15 pixels below the text
        draw.line([(name_start_x, underline_y_name), (name_end_x, underline_y_name)], fill=text_color, width=8)
        y += 70

    # 4. Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    bbox_wm = draw.textbbox((0, 0), watermark, font=watermark_font)
    draw.text((width//2, height - 80), watermark, font=watermark_font, fill=(200,200,200), anchor='mt')

    return img
