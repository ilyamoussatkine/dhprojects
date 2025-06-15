# /System/Library/Fonts/Supplemental/Georgia.ttf
# '/System/Library/Fonts/Supplemental/Georgia Bold.ttf'
# MARGIN_TOP = 700 - без виджетов
# MARGIN_TOP = 900 (910-920) - с виджетами
# MARGIN_BOTTOM = 200 - без виджетов  
# MARGIN_BOTTOM = 400 - с виджетами (фонарик, камера)

import os
import random
import json
from io import BytesIO
from flask import Flask, render_template, request, send_file
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps

app = Flask(__name__)

# Загрузка корпуса стихов
with open('poems.json', 'r', encoding='utf-8') as f:
    poems = json.load(f)

# Настройки
SCREEN_WIDTH = 1170
SCREEN_HEIGHT = 2532
MARGIN_SIDES = 120
LINE_SPACING = 40
MIN_FONT_SIZE = 30
MAX_FONT_SIZE = 50

DARK_COLORS = [
    {'name': 'Чёрный', 'value': (10, 10, 10)},
    {'name': 'Тёмно-синий', 'value': (25, 35, 50)},
    {'name': 'Тёмно-зелёный', 'value': (30, 45, 35)},
    {'name': 'Тёмно-бордовый', 'value': (50, 25, 30)},
    {'name': 'Тёмно-фиолетовый', 'value': (40, 30, 50)}
]

def load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()


def get_text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def choose_poem(authors):
    poems_by_author = [p for p in poems if p["author"] in authors]
    return random.choice(poems_by_author) if poems_by_author else random.choice(poems)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        authors = request.form.getlist("authors")
        poem = choose_poem(authors)
        lines = poem["text"].split("\n")

        has_widgets_top = "has_widgets_top" in request.form
        has_widgets_bottom = "has_widgets_bottom" in request.form

        margin_top = 920 if has_widgets_top else 700
        margin_bottom = 400 if has_widgets_bottom else 200

        bg_type = request.form.get("bg_type", "color")

        bg_image = None
        if bg_type == "custom" and 'bg_file' in request.files:
            uploaded_file = request.files["bg_file"]
            if uploaded_file and uploaded_file.filename:
                try:
                    bg_image = Image.open(uploaded_file.stream).convert("RGB")
                    bg_image = ImageOps.fit(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                    bg_image = ImageEnhance.Brightness(bg_image).enhance(0.45)  # процент затемнения 1 - ...
                except:
                    bg_image = None

        if not bg_image:
            try:
                bg_index = int(request.form.get("bg_color", 0))
                bg_color = DARK_COLORS[bg_index]["value"]
            except:
                bg_color = (0, 0, 0)
            bg_image = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), color=bg_color)

        draw = ImageDraw.Draw(bg_image)

        font_size = random.randint(MIN_FONT_SIZE, MAX_FONT_SIZE)
        title_font = load_font("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", min(font_size + 10, 60))
        text_font = load_font("/System/Library/Fonts/Supplemental/Georgia.ttf", font_size)
        author_font = load_font("/System/Library/Fonts/Supplemental/Georgia Italic.ttf", min(font_size + 2, 50))

        y = margin_top
        title_bbox = draw.textbbox((0, 0), poem["title"], font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((SCREEN_WIDTH - title_width) // 2, y), poem["title"], font=title_font, fill=(255, 255, 255))
        y += get_text_height(draw, poem["title"], title_font) + LINE_SPACING * 2
        
        # перенос даты из последней строки, если она прилипла
        if lines:
            last_line = lines[-1]
            if "." in last_line:
                parts = last_line.rsplit(".", 1)
                if len(parts) == 2 and parts[1].strip()[:1].isdigit():
                    lines[-1] = parts[0] + "."
                    lines.append("")  # пустая строка
                    lines.append(parts[1].strip())
        
        for line in lines:
            draw.text((MARGIN_SIDES, y), line, font=text_font, fill=(255, 255, 255))
            y += get_text_height(draw, line, text_font) + LINE_SPACING

        y += LINE_SPACING
        author_text = f"{poem['author']}"
        author_bbox = draw.textbbox((0, 0), author_text, font=author_font)
        author_width = author_bbox[2] - author_bbox[0]
        draw.text((SCREEN_WIDTH - MARGIN_SIDES - author_width, SCREEN_HEIGHT - margin_bottom), author_text, font=author_font, fill=(255, 255, 255))

        output = BytesIO()
        bg_image.save(output, format="PNG")
        output.seek(0)
        return send_file(output, mimetype="image/png", as_attachment=True, download_name="poetic_wallpaper.png")

    author_list = sorted(set(p["author"] for p in poems))
    return render_template("index.html", authors=author_list, colors=DARK_COLORS)

if __name__ == '__main__':
    app.run(debug=True)