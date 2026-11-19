from pathlib import Path

import numpy as np
import pytest

from converter.detect import ChartNotFound
from converter.pipeline import UnreadableImage, analyze
from converter.recognize import recognize
from converter.render import A4_PX, render_chart, to_pdf, to_png
from converter.scales import SCALES, occupancy

ROOT = Path(__file__).resolve().parent.parent
REFERENCE_CHART = ROOT / "reference-chart.png"
FADED_PHOTO = ROOT / "faded-photo.png"

needs_reference_chart = pytest.mark.skipif(not REFERENCE_CHART.exists(), reason="reference chart photo not present")
needs_faded_photo = pytest.mark.skipif(not FADED_PHOTO.exists(), reason="faded chart photo not present")


@needs_reference_chart
def test_reference_chart_is_read_dot_for_dot():
    analysis = analyze(REFERENCE_CHART.read_bytes())
    assert (analysis.detection.occupancy == np.array(occupancy(SCALES["ionian"]))).all()
    assert analysis.recognition.scale_key == "ionian"


@needs_reference_chart
def test_reference_chart_is_recognised_from_colours_alone():
    analysis = analyze(REFERENCE_CHART.read_bytes())
    recognition = recognize(analysis.detection, texts=[])
    assert (recognition.scale_key, recognition.method) == ("ionian", "colors")


@needs_faded_photo
def test_faded_low_resolution_photo_is_read_dot_for_dot():
    analysis = analyze(FADED_PHOTO.read_bytes())
    assert (analysis.detection.occupancy == np.array(occupancy(SCALES["mixolydian"]))).all()
    assert (analysis.recognition.scale_key, analysis.recognition.method) == ("mixolydian", "title")


@needs_faded_photo
def test_grey_modal_chart_without_a_title_stays_undecided():
    analysis = analyze(FADED_PHOTO.read_bytes())
    recognition = recognize(analysis.detection, texts=[])
    assert recognition.scale_key is None
    assert "mixolydian" in recognition.candidates


@pytest.mark.parametrize("scale_key", list(SCALES))
def test_generated_chart_round_trips(scale_key):
    scale = SCALES[scale_key]
    analysis = analyze(to_png(render_chart(scale)))
    assert (analysis.detection.occupancy == np.array(occupancy(scale))).all()
    assert analysis.recognition.scale_key == scale_key
    assert recognize(analysis.detection, texts=[]).scale_key == scale_key


def test_output_is_a4_at_300_dpi():
    image = render_chart(SCALES["dorian"])
    assert image.size == A4_PX == (2480, 3508)
    assert b"/MediaBox [ 0 0 595.2 841.92 ]" in to_pdf(image)


def test_rejects_files_that_are_not_charts():
    with pytest.raises(UnreadableImage):
        analyze(b"not an image")
    blank = np.full((600, 450, 3), 255, dtype=np.uint8)
    import cv2

    with pytest.raises(ChartNotFound):
        analyze(cv2.imencode(".png", blank)[1].tobytes())
