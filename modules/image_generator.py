# modules/image_generator.py
import os
import logging
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

def reshape_urdu(text):
    """Properly shape Urdu text for rendering."""
    if not text:
        return ""
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception as e:
        logging.error(f"Urdu shaping error: {e}")
        return text

def get_font(font_name, size):
    """Try to load font from static/fonts, fallback to default."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    font_path = os.path.join(base_dir, 'static', 'fonts', font_name)
    try:
        return ImageFont.truetype(font_path, size)
    except Exception as e:
        logging.warning(f"Could not load font {font_name}: {e}")
        return ImageFont.load_default()

def generate_ghazal_card(ghazal, verses, dedicator, dedicatee):
    """
    Returns a PIL Image object with the ghazal card.
    """
    # Dimensions (Instagram story size)
    width = 1080
    margin = 80
    line_spacing = 80      # space between lines
    verse_spacing = 100    # space between verses

    # Load fonts
    urdu_font = get_font('JameelNooriNastaleeq.ttf', 48)
    title_font = get_font('LiberationSerif-Bold.ttf', 44)
    poet_font = get_font('LiberationSerif-Italic.ttf', 36)
    dedication_font = get_font('LiberationSerif-Bold.ttf', 38)

    # Estimate total height
    y = 200  # start Y
    lines = []

    # Title (English)
    title_en = ghazal.get('title_english', 'Untitled')
    lines.append((title_en, title_font, (212, 175, 55)))

    # Title (Urdu)
    title_ur = ghazal.get('title_urdu', '')
    if title_ur:
        reshaped_title = reshape_urdu(title_ur)
        lines.append((reshaped_title, urdu_font, (255, 255, 255)))

    # Poet name
    poet = ghazal.get('poet_name', '')
    lines.append((poet, poet_font, (212, 175, 55)))

    # Add space before verses
    y += 100

    # Verses
    for verse in verses:
        misra1 = reshape_urdu(verse['misra1_urdu'])
        misra2 = reshape_urdu(verse['misra2_urdu'])
        lines.append((misra1, urdu_font, (255, 255, 255)))
        lines.append((misra2, urdu_font, (255, 255, 255)))
        lines.append(("", None, None))  # spacer between verses

    # Remove last spacer
    if lines and lines[-1][0] == "":
        lines.pop()

    # Dedication block
    if dedicator and dedicatee:
        lines.append(("", None, None))  # spacer
        ded_text = f"Shared by : {dedicator}"
        ded_to_text = f"Dedicated to : {dedicatee}"
        lines.append((ded_text, dedication_font, (212, 175, 55)))
        lines.append((ded_to_text, dedication_font, (255, 255, 255)))

    # Calculate total height
    for text, font, _ in lines:
        if text:
            bbox = font.getbbox(text) if hasattr(font, 'getbbox') else (0, 0, 0, font.getsize(text)[1])
            line_height = bbox[3] - bbox[1] if len(bbox) > 3 else font.getsize(text)[1]
            y += line_height + line_spacing
        else:
            y += verse_spacing

    y += 100  # bottom margin
    height = max(y, 1920)  # ensure minimum height

    # Create image with gradient background
    from PIL import ImageDraw
    img = Image.new('RGB', (width, height), (20, 20, 30))
    draw = ImageDraw.Draw(img)

    # Draw gradient (optional)
    for i in range(height):
        ratio = i / height
        r = int(20 * (1 - ratio) + 40 * ratio)
        g = int(20 * (1 - ratio) + 35 * ratio)
        b = int(30 * (1 - ratio) + 45 * ratio)
        draw.rectangle([(0, i), (width, i+1)], fill=(r, g, b))

    # Reset Y for drawing
    y = 200

    # Draw each line
    for text, font, color in lines:
        if not text:
            y += verse_spacing
            continue
        # Get text width for centering
        bbox = font.getbbox(text) if hasattr(font, 'getbbox') else (0, 0, 0, font.getsize(text)[1])
        text_width = bbox[2] - bbox[0] if len(bbox) > 2 else font.getsize(text)[0]
        x = (width - text_width) // 2
        draw.text((x, y), text, font=font, fill=color)
        # Advance Y
        line_height = bbox[3] - bbox[1] if len(bbox) > 3 else font.getsize(text)[1]
        y += line_height + line_spacing

    # Watermark
    watermark = "UCPC Poetry Archive • Preserving Urdu Poetry"
    draw.text((width // 2, height - 60), watermark, fill=(150, 150, 150), anchor='mt', font=ImageFont.load_default())

    return img