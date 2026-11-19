"""Web interface: upload a photo of a scale chart, get a clean printable A4 chart."""

import base64
import io
import os
import secrets
import socket
import threading
import webbrowser
import zipfile
from collections import OrderedDict
from functools import lru_cache

from flask import Flask, abort, jsonify, render_template, request, send_file

from converter.pipeline import ChartNotFound, UnreadableImage, analyze
from converter.render import render_chart, render_grids, to_pdf, to_png
from converter.scales import SCALES, Degree

MAX_UPLOAD_BYTES = 30 * 1024 * 1024
MAX_STORED_PHOTO_CHARTS = 20
MIME_TYPES = {"png": "image/png", "pdf": "application/pdf"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

# Charts copied dot-for-dot from photos that match no known scale, keyed by a random token.
_photo_charts = OrderedDict()


@lru_cache(maxsize=32)
def _scale_file(scale_key: str, extension: str) -> bytes:
    image = render_chart(SCALES[scale_key])
    return to_png(image) if extension == "png" else to_pdf(image)


def _file_name(name: str, extension: str) -> str:
    return f"{name.lower().replace(' ', '-')}-12-positions-A4.{extension}"


def _send(data: bytes, name: str, extension: str):
    return send_file(
        io.BytesIO(data),
        mimetype=MIME_TYPES[extension],
        as_attachment=request.args.get("download") == "1",
        download_name=_file_name(name, extension),
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/scales")
def list_scales():
    return jsonify(
        [{"key": s.key, "name": s.name, "subtitle": s.subtitle, "formula": s.formula} for s in SCALES.values()]
    )


@app.get("/api/chart/<scale_key>.<extension>")
def scale_chart(scale_key, extension):
    if scale_key not in SCALES or extension not in MIME_TYPES:
        abort(404)
    return _send(_scale_file(scale_key, extension), SCALES[scale_key].name, extension)


@app.get("/api/photo-chart/<token>.<extension>")
def photo_chart(token, extension):
    if token not in _photo_charts or extension not in MIME_TYPES:
        abort(404)
    title, grids = _photo_charts[token]
    image = render_grids(title, "", [Degree(n) for n in range(1, 8)], grids)
    return _send(to_png(image) if extension == "png" else to_pdf(image), title, extension)


@app.get("/api/all.zip")
def all_charts():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for scale in SCALES.values():
            archive.writestr(_file_name(scale.name, "pdf"), _scale_file(scale.key, "pdf"))
            archive.writestr(_file_name(scale.name, "png"), _scale_file(scale.key, "png"))
    buffer.seek(0)
    return send_file(buffer, mimetype="application/zip", as_attachment=True, download_name="scales-12-positions-A4.zip")


@app.post("/api/analyze")
def analyze_photo():
    upload = request.files.get("photo")
    if upload is None:
        return jsonify({"ok": False, "error": "no_file"}), 400
    try:
        analysis = analyze(upload.read())
    except UnreadableImage:
        return jsonify({"ok": False, "error": "unreadable_image"}), 422
    except ChartNotFound:
        return jsonify({"ok": False, "error": "chart_not_found"}), 422

    recognition = analysis.recognition
    token = secrets.token_urlsafe(12)
    _photo_charts[token] = (recognition.title_text or "Chart", analysis.grids)
    while len(_photo_charts) > MAX_STORED_PHOTO_CHARTS:
        _photo_charts.popitem(last=False)

    return jsonify(
        {
            "ok": True,
            "scale": recognition.scale_key,
            "method": recognition.method,
            "candidates": recognition.candidates,
            "shapeAgreement": round(recognition.shape_agreement, 4),
            "titleText": recognition.title_text,
            "titleScale": recognition.title_scale_key,
            "dots": int(analysis.detection.occupancy.sum()),
            "photoChartToken": token,
            "overlay": "data:image/jpeg;base64," + base64.b64encode(analysis.overlay_jpeg).decode("ascii"),
        }
    )


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"ok": False, "error": "file_too_large"}), 413


def _skip_reverse_dns_lookup():
    # http.server resolves the bind address through reverse DNS while starting, which can stall
    # for tens of seconds on machines where that lookup times out.
    socket.getfqdn = lambda name="": name or "localhost"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5050"))
    url = f"http://127.0.0.1:{port}/"
    _skip_reverse_dns_lookup()
    print(f"Fretprint is running at {url} (Ctrl+C to stop)")
    if os.environ.get("OPEN_BROWSER", "1") == "1":
        threading.Timer(1.0, webbrowser.open, args=(url,)).start()
    app.run(host="127.0.0.1", port=port, debug=False)
