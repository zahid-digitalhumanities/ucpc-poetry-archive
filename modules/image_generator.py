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
    poet_name_font = get_font('LiberationSerif-Bold.ttf', 56)
    poet_eng_font = get_font('LiberationSerif-BoldItalic.ttf', 44)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 44)
    watermark_font = get_font('LiberationSerif-Regular.ttf', 28)

    img = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # 1. Gold frame
    frame_width = 15
    draw.rectangle([frame_width, frame_width, width - frame_width, height - frame_width],
                   outline=gold, width=frame_width)

    y = 120

    # 2. Poet name (Urdu and English) at the top, with thick gold underline
    poet_ur = ghazal.get('poet_name_urdu', '').upper()
    poet_en = ghazal.get('poet_name', '').upper()
    if poet_ur:
        draw_centered_text(draw, poet_ur, y, poet_name_font, gold, width)
        y += 80
    if poet_en:
        draw_centered_text(draw, poet_en, y, poet_eng_font, dark_gray, width)
        y += 50
    # Thick underline below poet name (width 10)
    underline_y = y - 20
    draw.line([(200, underline_y), (width - 200, underline_y)], fill=gold, width=10)
    y += 80

    # 3. First couplet – both misras on the same line (horizontally)
    if verses:
        first_verse = verses[0]
        misra1 = first_verse.get('misra1_urdu', '')
        misra2 = first_verse.get('misra2_urdu', '')
        if misra1 and misra2:
            gap = 80
            bbox1 = draw.textbbox((0, 0), misra1, font=urdu_font)
            bbox2 = draw.textbbox((0, 0), misra2, font=urdu_font)
            width1 = bbox1[2] - bbox1[0]
            width2 = bbox2[2] - bbox2[0]
            total_width = width1 + gap + width2
            start_x = (width - total_width) // 2
            draw.text((start_x + width2 + gap, y), misra1, font=urdu_font, fill=text_color, anchor='rt')
            draw.text((start_x + width2, y), misra2, font=urdu_font, fill=text_color, anchor='lt')
            y += 100
        elif misra1:
            draw_centered_text(draw, misra1, y, urdu_font, text_color, width)
            y += 80
    else:
        y += 80

    y += 40

    # 4. Dedication section
    if dedicator and dedicatee:
        draw_centered_text(draw, f"From: {dedicator}", y, dedication_font, gold, width)
        y += 70
        ded_text = f"Dedicated to: {dedicatee}"
        bbox_full = draw.textbbox((0, 0), ded_text, font=dedication_font)
        full_width = bbox_full[2] - bbox_full[0]
        x_center = (width - full_width) // 2
        draw.text((x_center, y), ded_text, font=dedication_font, fill=text_color)
        # Thick underline under the recipient's name (width 8)
        prefix = "Dedicated to: "
        prefix_bbox = draw.textbbox((0, 0), prefix, font=dedication_font)
        name_bbox = draw.textbbox((0, 0), dedicatee, font=dedication_font)
        name_width = name_bbox[2] - name_bbox[0]
        name_start_x = x_center + (prefix_bbox[2] - prefix_bbox[0])
        name_end_x = name_start_x + name_width
        draw.line([(name_start_x, y + 10), (name_end_x, y + 10)], fill=text_color, width=8)
        y += 80

    # 5. Remaining verses (from second couplet onward) – each misra on its own line, reduced spacing
    for verse in verses[1:]:
        misra1 = verse.get('misra1_urdu', '')
        misra2 = verse.get('misra2_urdu', '')
        if misra1:
            draw_centered_text(draw, misra1, y, urdu_font, text_color, width, line_spacing=5)
            y += 55
        if misra2:
            draw_centered_text(draw, misra2, y, urdu_font, text_color, width, line_spacing=5)
            y += 45
        y += 25

    # 6. Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw_centered_text(draw, watermark, height - 100, watermark_font, (200,200,200), width)

    return img
