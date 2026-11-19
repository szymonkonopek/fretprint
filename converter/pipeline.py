"""Photo in, recognised chart out."""

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps

from .detect import ChartNotFound, Detection, detect_chart, draw_overlay
from .recognize import Recognition, observed_grids, read_texts, recognize

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
except ImportError:
    pass


class UnreadableImage(Exception):
    pass


@dataclass
class Analysis:
    recognition: Recognition
    detection: Detection
    overlay_jpeg: bytes
    grids: list


def _decode(data: bytes) -> np.ndarray:
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    except Exception as error:
        raise UnreadableImage(str(error)) from error
    return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)


def analyze(data: bytes) -> Analysis:
    """Raises UnreadableImage or ChartNotFound when the photo cannot be used."""
    image = _decode(data)
    detection = detect_chart(image)
    recognition = recognize(detection, read_texts(detection.work_image))
    encoded, overlay = cv2.imencode(".jpg", draw_overlay(detection), [cv2.IMWRITE_JPEG_QUALITY, 82])
    return Analysis(recognition, detection, overlay.tobytes() if encoded else b"", observed_grids(detection))


__all__ = ["Analysis", "ChartNotFound", "UnreadableImage", "analyze"]
