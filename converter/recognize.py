"""Works out which scale a photographed chart shows.

Three independent clues are combined: the dot layout, the printed title read
by OCR, and the dot colours. All seven modes of the major scale share one dot
layout, so the layout alone only narrows the answer down to a family.
"""

import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from functools import lru_cache

import cv2
import numpy as np

from .detect import Detection
from .render import DEGREE_COLORS
from .scales import SCALES, Degree, chart_grids, occupancy

SHAPE_MATCH_MINIMUM = 0.88
SHAPE_TIE_MARGIN = 0.015
TITLE_MATCH_MINIMUM = 0.72
CHROMATIC_MINIMUM = 22.0
CHROMATIC_SHARE_FOR_COLOR_VOTE = 0.5

TITLE_ALIASES = {
    "naturalminor": "aeolian",
    "majorpentatonic": "major_pentatonic",
    "minorpentatonic": "minor_pentatonic",
    "harmonicminor": "harmonic_minor",
}


@dataclass
class Recognition:
    scale_key: str = None
    method: str = "none"
    shape_agreement: float = 0.0
    candidates: list = field(default_factory=list)
    title_text: str = ""
    title_scale_key: str = None
    has_colors: bool = False


@lru_cache(maxsize=1)
def _ocr_engine():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def read_texts(image_bgr: np.ndarray) -> list:
    result, _ = _ocr_engine()(image_bgr)
    return [(text, float(confidence)) for _, text, confidence in (result or [])]


def _letters(text: str) -> str:
    return re.sub(r"[^a-z]", "", text.lower())


def _title_vote(texts: list):
    """Pick the scale whose name the OCR output repeats most convincingly."""
    names = {_letters(scale.name): key for key, scale in SCALES.items()}
    names.update(TITLE_ALIASES)
    votes = {}
    best_text = {}
    for text, confidence in texts:
        letters = _letters(text)
        if len(letters) < 4:
            continue
        ratio, key = max((SequenceMatcher(None, letters, name).ratio(), key) for name, key in names.items())
        if ratio >= TITLE_MATCH_MINIMUM:
            votes[key] = votes.get(key, 0.0) + ratio * confidence
            best_text.setdefault(key, text)
    if not votes:
        return None, ""
    key = max(votes, key=votes.get)
    return key, best_text[key]


def _palette_lab() -> dict:
    swatch = np.array([[DEGREE_COLORS[n][::-1] for n in sorted(DEGREE_COLORS)]], dtype=np.uint8)
    lab = cv2.cvtColor(swatch, cv2.COLOR_BGR2LAB).astype(np.float32)[0]
    return {number: lab[index] for index, number in enumerate(sorted(DEGREE_COLORS))}


def _degree_numbers_from_colors(detection: Detection):
    """Nearest palette colour for every chromatic dot; 0 where the dot is grey or absent."""
    palette = _palette_lab()
    numbers = np.zeros(detection.occupancy.shape, dtype=int)
    chromatic = 0
    for index, diagram in enumerate(detection.diagrams):
        for row, string in zip(*np.nonzero(diagram.dots)):
            color = diagram.colors[row, string]
            if np.hypot(color[1] - 128, color[2] - 128) < CHROMATIC_MINIMUM:
                continue
            chromatic += 1
            numbers[index, row, string] = min(palette, key=lambda n: np.linalg.norm(palette[n] - color))
    total = int(detection.occupancy.sum())
    return numbers, (chromatic / total if total else 0.0)


def _color_agreement(numbers: np.ndarray, scale_key: str) -> float:
    grids = chart_grids(SCALES[scale_key])
    hits = total = 0
    for index, row, string in zip(*np.nonzero(numbers)):
        degree = grids[index][row][string]
        if degree is None:
            continue
        total += 1
        hits += degree.number == numbers[index, row, string]
    return hits / total if total else 0.0


def recognize(detection: Detection, texts: list) -> Recognition:
    observed = detection.occupancy
    agreement = {key: float((np.array(occupancy(scale)) == observed).mean()) for key, scale in SCALES.items()}
    best = max(agreement.values())
    candidates = [key for key, value in agreement.items() if value >= best - SHAPE_TIE_MARGIN]
    title_key, title_text = _title_vote(texts)
    numbers, chromatic_share = _degree_numbers_from_colors(detection)
    has_colors = chromatic_share >= CHROMATIC_SHARE_FOR_COLOR_VOTE

    result = Recognition(
        shape_agreement=best,
        candidates=candidates,
        title_text=title_text,
        title_scale_key=title_key,
        has_colors=has_colors,
    )
    if best < SHAPE_MATCH_MINIMUM:
        return result
    if title_key in candidates:
        result.scale_key, result.method = title_key, "title"
    elif has_colors:
        result.scale_key = max(candidates, key=lambda key: _color_agreement(numbers, key))
        result.method = "colors"
    elif len(candidates) == 1:
        result.scale_key, result.method = candidates[0], "shape"
    return result


def observed_grids(detection: Detection) -> list:
    """Dots exactly as photographed, coloured by their nearest palette colour.

    Used for charts that match no known scale. Grey dots get degree 1 because
    the photo carries no information to tell them apart.
    """
    numbers, _ = _degree_numbers_from_colors(detection)
    grids = []
    for index, diagram in enumerate(detection.diagrams):
        grid = []
        for row in range(diagram.dots.shape[0]):
            cells = []
            for string in range(diagram.dots.shape[1]):
                if diagram.dots[row, string]:
                    cells.append(Degree(int(numbers[index, row, string]) or 1))
                else:
                    cells.append(None)
            grid.append(cells)
        grids.append(grid)
    return grids
