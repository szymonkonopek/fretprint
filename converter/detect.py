"""Reads a photographed 12-position chart: finds the 12 fretboard grids and their dots."""

from dataclasses import dataclass, field

import cv2
import numpy as np

from .scales import POSITIONS, ROWS, STRINGS

WORK_WIDTH = 1400
COLUMNS = 4
CHART_ROWS = 3
# Row height divided by string spacing on the printed charts.
ROW_TO_STRING_RATIO = 1.6
DOT_RADIUS_TO_STRING = 0.44


class ChartNotFound(Exception):
    pass


@dataclass
class Diagram:
    # (ROWS, STRINGS, 2) array of x, y centres of every string/row crossing
    points: np.ndarray
    string_gap: float
    row_gap: float
    dots: np.ndarray
    colors: np.ndarray


@dataclass
class Detection:
    diagrams: list
    work_image: np.ndarray
    line_contrast: np.ndarray = field(default=None)
    paper_distance: np.ndarray = field(default=None)

    @property
    def occupancy(self) -> np.ndarray:
        return np.array([d.dots for d in self.diagrams])


def _runs(active: np.ndarray, min_length: int, max_gap: int) -> list:
    runs = []
    start = None
    last_on = None
    for index, on in enumerate(active):
        if on:
            if start is None:
                start = index
            last_on = index
        elif start is not None and index - last_on > max_gap:
            if last_on - start + 1 >= min_length:
                runs.append((start, last_on))
            start = None
    if start is not None and last_on - start + 1 >= min_length:
        runs.append((start, last_on))
    return runs


def _stroke_masks(gray: np.ndarray):
    """Thin dark strokes only: grid lines and dot outlines, without filled dots.

    The opening kernels are shorter than one grid cell so that slightly tilted
    lines survive them.
    """
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    blackhat = cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel)
    _, strokes = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    horizontal = cv2.morphologyEx(strokes, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (34, 1)))
    vertical = cv2.morphologyEx(strokes, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 45)))
    return horizontal, vertical


def _best_comb(profile: np.ndarray, teeth: int, start_range, gap_range, guard_teeth: bool) -> tuple:
    """Fit `teeth` equally spaced peaks to a 1-D profile; returns (start, gap).

    Each tooth contributes at most half of the profile maximum so that every
    tooth has to land on a line. Guard teeth one step outside the comb must
    stay empty, which rejects fits shifted by a whole step.
    """
    smooth = np.convolve(profile, np.ones(5) / 5, mode="same")
    capped = np.minimum(smooth, smooth.max() * 0.5)
    best = (-np.inf, start_range[0], gap_range[0])
    for gap in np.arange(gap_range[0], gap_range[1] + 0.01, 0.5):
        offsets = np.arange(teeth) * gap
        for start in np.arange(start_range[0], start_range[1] + 0.01, 1.0):
            positions = np.round(start + offsets).astype(int)
            if positions[0] < 0 or positions[-1] >= len(capped):
                continue
            score = capped[positions].sum()
            if guard_teeth:
                for guard in (int(round(start - gap)), int(round(start + teeth * gap))):
                    if 0 <= guard < len(capped):
                        score -= capped[guard]
            if score > best[0]:
                best = (score, start, gap)
    return best[1], best[2]


def _column_bands(horizontal: np.ndarray) -> list:
    """Horizontal extents of the four diagram columns.

    Counts separate lines rather than pixels: a column stacks 21 fret lines,
    while the thick strokes of a large page title add only two or three.
    """
    width = horizontal.shape[1]
    on = horizontal > 0
    line_count = (on[1:] & ~on[:-1]).sum(axis=0).astype(float)
    profile = np.convolve(line_count, np.ones(5) / 5, mode="same")
    return _runs(profile > profile.max() * 0.25, min_length=width // 14, max_gap=12)


def _diagram_spans(vertical: np.ndarray, band) -> list:
    left, right = band
    row_gap = (right - left) / (STRINGS - 1) * ROW_TO_STRING_RATIO
    profile = (vertical[:, left : right + 1] > 0).sum(axis=1)
    # A dot hides its string for 0.56 of a row; the label strip between diagrams is a full row tall.
    return _runs(profile >= 2, min_length=int(row_gap * 4), max_gap=int(row_gap * 0.8))


def _fit_strings(vertical: np.ndarray, y_range, x_window, start_range, gap_range):
    y0, y1 = y_range
    x0, x1 = x_window
    profile = (vertical[y0:y1, x0:x1] > 0).sum(axis=0).astype(float)
    start, gap = _best_comb(
        profile, STRINGS, (start_range[0] - x0, start_range[1] - x0), gap_range, guard_teeth=True
    )
    return x0 + start, gap


def _fit_frets(horizontal: np.ndarray, vertical: np.ndarray, x_range, start_range, gap_range):
    """Find the top fret line and the row height of one diagram.

    Combines the comb of seven fret lines with the vertical extent of the
    strings: strings run exactly from the first to the last fret line.
    """
    xa, xb = x_range
    line_profile = np.convolve((horizontal[:, xa:xb] > 0).sum(axis=1).astype(float), np.ones(5) / 5, mode="same")
    reference = line_profile[max(0, int(start_range[0])) : int(start_range[1] + (ROWS + 1) * gap_range[1])]
    cap = max(1.0, reference.max() * 0.5) if reference.size else 1.0
    capped = np.minimum(line_profile, cap) / cap
    strings_present = ((vertical[:, xa:xb] > 0).sum(axis=1) >= 4).astype(float)
    cumulative = np.concatenate([[0.0], np.cumsum(strings_present)])
    size = len(capped)

    def presence(a, b):
        a, b = int(max(0, min(size, a))), int(max(0, min(size, b)))
        return (cumulative[b] - cumulative[a]) / (b - a) if b > a else 0.0

    def tooth(y):
        y = int(round(y))
        return capped[y] if 0 <= y < size else 0.0

    best = (-np.inf, start_range[0], gap_range[0])
    for gap in np.arange(gap_range[0], gap_range[1] + 0.01, 0.5):
        for start in np.arange(start_range[0], start_range[1] + 0.01, 1.0):
            end = start + ROWS * gap
            if start < 0 or end >= size:
                continue
            score = sum(tooth(start + k * gap) for k in range(ROWS + 1))
            score -= tooth(start - gap) + tooth(end + gap)
            score += 4.0 * presence(start, end)
            score -= 2.0 * (presence(start - gap, start - 0.15 * gap) + presence(end + 0.15 * gap, end + gap))
            if score > best[0]:
                best = (score, start, gap)
    return best[1], best[2]


def _refine_grid(horizontal: np.ndarray, vertical: np.ndarray, band, span) -> tuple:
    """Fit the 6x6 lattice of one diagram; returns (points, string_gap, row_gap).

    Strings are fitted separately in the upper and lower half and frets in the
    left and right half, so a tilted or perspective-distorted diagram still gets
    every crossing in the right place.
    """
    left, right = band
    top, bottom = span
    height, width = horizontal.shape
    band_gap = (right - left) / (STRINGS - 1)
    # The band can miss an outer string when the photo crops it, so search more than one string wide.
    slack_x = int(band_gap * 1.3)
    x_window = (max(0, left - slack_x - 5), min(width, right + slack_x + 5))
    x_start, string_gap = _fit_strings(
        vertical, (top, bottom), x_window, (left - slack_x, left + slack_x), (band_gap * 0.85, band_gap * 1.15)
    )

    # Dots can hide the strings in the first or last row and the page title can extend a span
    # upwards, so the span only brackets the frame; the row height itself follows the string gap.
    nominal_row_gap = string_gap * ROW_TO_STRING_RATIO
    earliest = max(0.0, top - 1.2 * nominal_row_gap)
    latest = max(top, bottom - ROWS * nominal_row_gap) + 1.2 * nominal_row_gap
    x_range = (max(0, int(x_start)), min(width, int(x_start + (STRINGS - 1) * string_gap)))
    y_start, row_gap = _fit_frets(
        horizontal, vertical, x_range, (earliest, latest), (nominal_row_gap * 0.95, nominal_row_gap * 1.05)
    )
    y_end = y_start + ROWS * row_gap
    y_mid = (y_start + y_end) / 2
    x_mid = x_start + (STRINGS - 1) * string_gap / 2

    tight_x = (x_start - 0.6 * string_gap, x_start + 0.6 * string_gap)
    tight_gap = (string_gap * 0.94, string_gap * 1.06)
    upper = _fit_strings(vertical, (max(0, int(y_start)), int(y_mid)), x_window, tight_x, tight_gap)
    lower = _fit_strings(vertical, (int(y_mid), min(height, int(y_end))), x_window, tight_x, tight_gap)
    y_upper, y_lower = (y_start + y_mid) / 2, (y_mid + y_end) / 2

    tight_y = (max(0.0, y_start - 0.3 * row_gap), y_start + 0.3 * row_gap)
    fixed_gap = (row_gap, row_gap)
    left_half = _fit_frets(horizontal, vertical, (x_range[0], int(x_mid)), tight_y, fixed_gap)
    right_half = _fit_frets(horizontal, vertical, (int(x_mid), x_range[1]), tight_y, fixed_gap)
    x_left, x_right = (x_range[0] + x_mid) / 2, (x_mid + x_range[1]) / 2
    fret_slope = (right_half[0] - left_half[0]) / (x_right - x_left)

    points = np.zeros((ROWS, STRINGS, 2))
    for row in range(ROWS):
        y_center = y_start + (row + 0.5) * row_gap
        blend = (y_center - y_upper) / (y_lower - y_upper)
        for string in range(STRINGS):
            x = (upper[0] + string * upper[1]) * (1 - blend) + (lower[0] + string * lower[1]) * blend
            y = left_half[0] + (x - x_left) * fret_slope + (row + 0.5) * row_gap
            points[row, string] = (x, y)
    return points, string_gap, row_gap


def _disk_offsets(radius: float, exclude_vertical_strip: float = 0.0):
    reach = int(np.ceil(radius))
    ys, xs = np.mgrid[-reach : reach + 1, -reach : reach + 1]
    keep = (np.hypot(xs, ys) <= radius) & (np.abs(xs) >= exclude_vertical_strip)
    return ys[keep], xs[keep]


def _sample(image: np.ndarray, cy: float, cx: float, offsets) -> np.ndarray:
    ys = np.clip(np.round(cy + offsets[0]).astype(int), 0, image.shape[0] - 1)
    xs = np.clip(np.round(cx + offsets[1]).astype(int), 0, image.shape[1] - 1)
    return image[ys, xs]


def _crossing_features(lab: np.ndarray, points: np.ndarray, string_gap: float, row_gap: float):
    """Measure every string/row crossing.

    Returns the fill colour, how strongly the string line shows through the
    centre (a dot covers it), and the colour distance between fill and paper.
    """
    radius = string_gap * DOT_RADIUS_TO_STRING
    fill_offsets = _disk_offsets(radius * 0.62, exclude_vertical_strip=radius * 0.3)
    patch_offsets = _disk_offsets(radius * 0.22)
    half_height = max(2, int(radius * 0.45))
    shift_reach = max(2, int(radius * 0.3))
    lightness = lab[:, :, 0]

    fills = np.zeros((ROWS, STRINGS, 3))
    line_contrast = np.zeros((ROWS, STRINGS))
    paper_distance = np.zeros((ROWS, STRINGS))
    for row in range(ROWS):
        for string in range(STRINGS):
            cx, cy = points[row, string]
            paper_samples = []
            for dx in (-0.5, 0.5):
                # Outside the frame the paper is white even next to a shaded row.
                if (string == 0 and dx < 0) or (string == STRINGS - 1 and dx > 0):
                    continue
                for dy in (-0.3, 0.3):
                    paper_samples.append(
                        _sample(lab, cy + dy * row_gap, cx + dx * string_gap, patch_offsets).reshape(-1, 3)
                    )
            paper = np.median(np.concatenate(paper_samples), axis=0)
            fill = np.median(_sample(lab, cy, cx, fill_offsets).reshape(-1, 3), axis=0)
            yc, xc = int(round(cy)), int(round(cx))
            window = lightness[
                max(0, yc - half_height) : yc + half_height + 1,
                max(0, xc - shift_reach) : xc + shift_reach + 1,
            ]
            fills[row, string] = fill
            line_contrast[row, string] = fill[0] - window.mean(axis=0).min() if window.size else 0.0
            paper_distance[row, string] = np.linalg.norm(fill - paper)
    return fills, line_contrast, paper_distance


LINE_VISIBLE_FRACTION = 0.45
CLEAR_FILL_DISTANCE = 40.0


def _classify(line_contrast: np.ndarray, paper_distance: np.ndarray) -> np.ndarray:
    """A crossing holds a dot when its string line is hidden or its fill clearly differs from paper.

    Roughly half of all crossings are empty, so a high percentile of the line
    contrast is the contrast of an uncovered string line in this photo.
    """
    uncovered_line = np.percentile(line_contrast, 80)
    return (line_contrast < uncovered_line * LINE_VISIBLE_FRACTION) | (paper_distance > CLEAR_FILL_DISTANCE)


def detect_chart(image_bgr: np.ndarray) -> Detection:
    scale = WORK_WIDTH / image_bgr.shape[1]
    interpolation = cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA
    work = cv2.resize(image_bgr, None, fx=scale, fy=scale, interpolation=interpolation)
    gray = cv2.cvtColor(work, cv2.COLOR_BGR2GRAY)
    horizontal, vertical = _stroke_masks(gray)

    bands = _column_bands(horizontal)
    if len(bands) != COLUMNS:
        raise ChartNotFound(f"expected {COLUMNS} columns of diagrams, found {len(bands)}")

    lab = cv2.cvtColor(cv2.GaussianBlur(work, (0, 0), 1.2), cv2.COLOR_BGR2LAB).astype(np.float32)
    lattices = []
    for band in bands:
        spans = _diagram_spans(vertical, band)
        if len(spans) != CHART_ROWS:
            raise ChartNotFound(f"expected {CHART_ROWS} diagrams in a column, found {len(spans)}")
        for span in spans:
            lattices.append(_refine_grid(horizontal, vertical, band, span))

    features = [_crossing_features(lab, *lattice) for lattice in lattices]
    line_contrast = np.array([f[1] for f in features])
    paper_distance = np.array([f[2] for f in features])
    dots = _classify(line_contrast, paper_distance)
    diagrams = [
        Diagram(points, string_gap, row_gap, dots[index], features[index][0])
        for index, (points, string_gap, row_gap) in enumerate(lattices)
    ]
    assert len(diagrams) == POSITIONS
    return Detection(diagrams, work, line_contrast, paper_distance)


def draw_overlay(detection: Detection) -> np.ndarray:
    """Debug view: detected crossings on the photo, dots in green, empty crossings in red."""
    overlay = detection.work_image.copy()
    for diagram in detection.diagrams:
        radius = int(diagram.string_gap * DOT_RADIUS_TO_STRING)
        for row in range(ROWS):
            for string in range(STRINGS):
                cx, cy = diagram.points[row, string]
                center = (int(round(cx)), int(round(cy)))
                if diagram.dots[row, string]:
                    cv2.circle(overlay, center, radius, (0, 170, 0), 3)
                else:
                    cv2.circle(overlay, center, 4, (0, 0, 230), -1)
    return overlay
