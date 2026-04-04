from PIL import Image, ImageDraw, ImageFont
import os
import logging

FONT_CACHE = {}

def get_font(font_name, size):
    key = (font_name, size)
    if key in FONT_CACHE:
        return FONT_CACHE[key]

    base_dir = os.path.dirname(os.path.dirname(__file__))
    font_path = os.path.join(base_dir, 'static', 'fonts', font_name)

    try:
        font = ImageFont.truetype(font_path, size)
    except:
        font = ImageFont.load_default()

    FONT_CACHE[key] = font
    return font


def draw_couplet(draw, m1, m2, y, font, width):
    text = f"{m1}    {m2}"
    draw.text((width - 50, y), text, font=font, fill="black", anchor="ra")
    return y + 60


def generate_ghazal_card(ghazal, verses):

    # ✅ FACEBOOK SAFE SIZE
    width, height = 1200, 630

    img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    title_font = get_font('JameelNooriNastaleeq.ttf', 42)
    text_font = get_font('JameelNooriNastaleeq.ttf', 28)

    y = 40

    # ======================
    # TITLE
    # ======================
    poet = ghazal.get('poet_name_urdu', '')
    draw.text((width//2, y), poet, font=title_font, fill="black", anchor="mm")
    y += 70

    # ======================
    # COMPACT GHAZAL
    # ======================
    for verse in verses:

        m1 = verse.get('misra1_urdu', '')
        m2 = verse.get('misra2_urdu', '')

        y = draw_couplet(draw, m1, m2, y, text_font, width)

        # ✅ overflow stop
        if y > height - 60:
            draw.text((width - 40, height - 40), "...", font=text_font, fill="gray", anchor="ra")
            break

    return img