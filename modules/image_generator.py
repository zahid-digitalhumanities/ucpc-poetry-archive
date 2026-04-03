import os
import logging
from PIL import Image, ImageDraw, ImageFont

# Urdu shaping
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    SHAPE_URDU = True
except:
    SHAPE_URDU = False

def shape_urdu(text):
    if SHAPE_URDU and text:
        try:
            return get_display(arabic_reshaper.reshape(text))
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
    except:
        font = ImageFont.load_default()

    FONT_CACHE[key] = font
    return font

# ✅ Inline couplet (main feature)
def draw_couplet_inline(draw, m1, m2, y, font, width, gap=40):
    m1 = shape_urdu(m1)
    m2 = shape_urdu(m2)

    bbox1 = draw.textbbox((0, 0), m1, font=font)
    bbox2 = draw.textbbox((0, 0), m2, font=font)

    w1 = bbox1[2] - bbox1[0]
    w2 = bbox2[2] - bbox2[0]

    total = w1 + gap + w2
    start_x = (width - total) // 2

    draw.text((start_x + w2 + gap, y), m1, font=font, fill=(0,0,0), anchor="rt")
    draw.text((start_x + w2, y), m2, font=font, fill=(0,0,0), anchor="lt")

    h = max(bbox1[3]-bbox1[1], bbox2[3]-bbox2[1])
    return y + h + 12   # tight spacing

def draw_center(draw, text, y, font, color, width):
    text = shape_urdu(text)
    bbox = draw.textbbox((0,0), text, font=font)
    x = (width - (bbox[2]-bbox[0])) // 2
    draw.text((x,y), text, font=font, fill=color)
    return y + (bbox[3]-bbox[1]) + 6

def generate_ghazal_card(ghazal, verses, dedicator='', dedicatee=''):

    # ✅ FACEBOOK SAFE SIZE
    width, height = 1080, 900

    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    gold = (212,175,55)

    # ✅ COMPACT FRAME
    draw.rectangle([10,10,width-10,height-10], outline=gold, width=5)

    # Fonts (compact)
    poet_font = get_font('JameelNooriNastaleeq.ttf', 36)
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 26)
    small_font = get_font('LiberationSerif-Regular.ttf', 18)

    y = 25

    # Poet name
    poet = ghazal.get('poet_name_urdu','')
    if poet:
        y = draw_center(draw, poet, y, poet_font, gold, width)

    draw.line([(200,y),(width-200,y)], fill=gold, width=3)
    y += 20

    # ✅ Find matla
    matla = None
    for v in verses:
        if v.get('misra1_urdu') and v.get('misra2_urdu'):
            matla = v
            break

    # ✅ Draw matla
    if matla:
        y = draw_couplet_inline(draw,
                               matla['misra1_urdu'],
                               matla['misra2_urdu'],
                               y, urdu_font, width)

    # ✅ Draw next 3–4 couplets
    count = 0
    for v in verses:
        if v == matla:
            continue

        if count >= 4:
            break

        m1 = v.get('misra1_urdu','')
        m2 = v.get('misra2_urdu','')

        if m1 and m2:
            y = draw_couplet_inline(draw, m1, m2, y, urdu_font, width)
            count += 1

        if y > height - 80:
            break

    # Dedication (compact)
    if dedicator and dedicatee:
        y += 5
        draw.text((40,y), f"From: {dedicator}", font=small_font, fill=gold)
        y += 20

        text = f"Dedicated to: {dedicatee}"
        draw.text((40,y), text, font=small_font, fill=(0,0,0))

        bbox = draw.textbbox((0,0), text, font=small_font)
        draw.line(
            [(40, y + bbox[3]-bbox[1] + 8),
             (40 + bbox[2]-bbox[0], y + bbox[3]-bbox[1] + 8)],
            fill=(0,0,0),
            width=2
        )

    # Footer
    draw_center(draw, "UCPC Poetry Archive", height-40, small_font, (120,120,120), width)

    return img