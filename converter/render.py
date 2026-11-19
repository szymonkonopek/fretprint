"""Renders a 12-position scale chart as an A4 portrait image."""

import io

from PIL import Image, ImageDraw, ImageFont

from .scales import GREY_ROWS, ROWS, STRINGS, Scale, chart_grids

DPI = 300
A4_PX = (2480, 3508)
SUPERSAMPLE = 2

DEGREE_COLORS = {
    1: (222, 52, 43),
    2: (240, 150, 52),
    3: (250, 231, 60),
    4: (78, 172, 72),
    5: (72, 163, 218),
    6: (38, 84, 148),
    7: (164, 146, 196),
}
INK = (26, 26, 26)
GREY_FILL = (216, 216, 216)
PAPER = (255, 255, 255)

FONT_CANDIDATES = (
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)

COLUMNS = 4
CHART_ROWS = 3


def _font(size: float):
    for path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, int(size))
        except OSError:
            continue
    return ImageFont.load_default(int(size))


def _text_color_on(fill):
    luminance = 0.299 * fill[0] + 0.587 * fill[1] + 0.114 * fill[2]
    return INK if luminance > 120 else PAPER


def _draw_dot(draw, cx, cy, radius, degree, outline_width, accidental_font):
    fill = DEGREE_COLORS[degree.number]
    draw.ellipse(
        (cx - radius, cy - radius, cx + radius, cy + radius),
        fill=fill,
        outline=INK,
        width=outline_width,
    )
    if degree.accidental:
        draw.text((cx, cy), degree.accidental, font=accidental_font, fill=_text_color_on(fill), anchor="mm")


def _draw_diagram(draw, left, top, string_gap, row_gap, grid, line_width, accidental_font):
    width = string_gap * (STRINGS - 1)
    height = row_gap * ROWS
    for row in GREY_ROWS:
        draw.rectangle((left, top + row * row_gap, left + width, top + (row + 1) * row_gap), fill=GREY_FILL)
    for string in range(STRINGS):
        x = left + string * string_gap
        draw.line((x, top, x, top + height), fill=INK, width=line_width)
    for fret in range(ROWS + 1):
        y = top + fret * row_gap
        half = line_width // 2
        draw.line((left - half, y, left + width + half, y), fill=INK, width=line_width)
    radius = string_gap * 0.44
    for row, cells in enumerate(grid):
        for string, degree in enumerate(cells):
            if degree is None:
                continue
            _draw_dot(
                draw,
                left + string * string_gap,
                top + (row + 0.5) * row_gap,
                radius,
                degree,
                max(2, line_width * 2 // 3),
                accidental_font,
            )


def _draw_header(draw, title, subtitle, degrees, page_width, top, unit):
    title_font = _font(unit * 2.5)
    subtitle_font = _font(unit * 0.95)
    legend_font = _font(unit * 0.62)
    accidental_font = _font(unit * 0.5)

    gap = unit * 0.9
    title_width = draw.textlength(title, font=title_font)
    subtitle_width = draw.textlength(subtitle, font=subtitle_font)
    total = title_width + (gap + subtitle_width if subtitle else 0)
    limit = page_width - 4 * unit
    if total > limit:
        title_font = _font(unit * 2.5 * limit / total)
        subtitle_font = _font(unit * 0.95 * limit / total)
        gap *= limit / total
        title_width = draw.textlength(title, font=title_font)
        subtitle_width = draw.textlength(subtitle, font=subtitle_font)
        total = title_width + (gap + subtitle_width if subtitle else 0)
    start = (page_width - total) / 2
    baseline = top + unit * 2.3
    draw.text((start, baseline), title, font=title_font, fill=INK, anchor="ls")
    draw.text((start + title_width + gap, baseline), subtitle, font=subtitle_font, fill=INK, anchor="ls")

    radius = unit * 0.36
    label_gap = unit * 0.14
    item_gap = unit * 0.55
    widths = [2 * radius + label_gap + draw.textlength(d.label, font=legend_font) for d in degrees]
    x = (page_width - sum(widths) - item_gap * (len(degrees) - 1)) / 2
    legend_y = baseline + unit * 1.05
    for degree, width in zip(degrees, widths):
        _draw_dot(draw, x + radius, legend_y, radius, degree, max(2, int(unit * 0.035)), accidental_font)
        draw.text((x + 2 * radius + label_gap, legend_y), degree.label, font=legend_font, fill=INK, anchor="lm")
        x += width + item_gap


def render_chart(scale: Scale) -> Image.Image:
    degrees = [scale.degrees[s] for s in sorted(scale.degrees)]
    return render_grids(scale.name, scale.subtitle, degrees, chart_grids(scale))


def render_grids(title: str, subtitle: str, legend_degrees: list, grids: list) -> Image.Image:
    k = SUPERSAMPLE
    page_w, page_h = A4_PX[0] * k, A4_PX[1] * k
    image = Image.new("RGB", (page_w, page_h), PAPER)
    draw = ImageDraw.Draw(image)

    string_gap = 82 * k
    row_gap = int(string_gap * 1.58)
    diagram_w = string_gap * (STRINGS - 1)
    diagram_h = row_gap * ROWS
    column_gap = int(string_gap * 2.0)
    label_h = int(string_gap * 1.25)
    block_gap = int(string_gap * 0.75)
    header_h = int(string_gap * 4.3)

    content_w = COLUMNS * diagram_w + (COLUMNS - 1) * column_gap
    content_h = header_h + CHART_ROWS * (label_h + diagram_h) + (CHART_ROWS - 1) * block_gap
    left_margin = (page_w - content_w) // 2
    top_margin = (page_h - content_h) // 2

    _draw_header(draw, title, subtitle, legend_degrees, page_w, top_margin, string_gap)

    label_font = _font(string_gap * 0.8)
    # One name size for all twelve labels: fit the name next to the widest position number.
    name_font = label_font
    name_room = diagram_w + string_gap * 0.2 - draw.textlength("12", font=label_font)
    name_w = draw.textlength(title, font=label_font)
    if name_w > name_room:
        name_font = _font(string_gap * 0.8 * name_room / name_w)
    accidental_font = _font(string_gap * 0.62)
    line_width = 5 * k
    for index, grid in enumerate(grids):
        column, chart_row = divmod(index, CHART_ROWS)
        left = left_margin + column * (diagram_w + column_gap)
        block_top = top_margin + header_h + chart_row * (label_h + diagram_h + block_gap)
        top = block_top + label_h
        label_baseline = top - string_gap * 0.42
        number = str(index + 1)
        draw.text((left - string_gap * 0.25, label_baseline), title, font=name_font, fill=INK, anchor="ls")
        draw.text((left + diagram_w + string_gap * 0.25, label_baseline), number, font=label_font, fill=INK, anchor="rs")
        _draw_diagram(draw, left, top, string_gap, row_gap, grid, line_width, accidental_font)

    return image.resize(A4_PX, Image.LANCZOS)


def to_png(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", dpi=(DPI, DPI), optimize=True)
    return buffer.getvalue()


def to_pdf(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PDF", resolution=DPI)
    return buffer.getvalue()
