# Fretprint

Turns a photo of a guitar scale chart (12 positions on one page) into a clean, colour-coded A4 chart ready to print. It can also generate a chart for any supported scale without a photo.

## Before and after

| Before: faded, low-resolution photo | After: generated A4 chart |
| :---: | :---: |
| <img src="docs/example-before.jpg" alt="Faded low-resolution photo of a Mixolydian chart" width="360"> | <img src="docs/example-after.png" alt="Clean colour-coded Mixolydian chart" width="360"> |

The photo is read dot for dot, the scale is recognised as Mixolydian, and the chart is redrawn with a colour per scale degree. The "before" image is a simulated photo: a generated chart with washed-out colours, blur, noise and a slight perspective tilt.

## Running it

macOS: double-click `start.command`. The first run installs the dependencies, then the browser opens at `http://127.0.0.1:5050/`.

Manually:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Environment variables: `PORT` (default 5050), `OPEN_BROWSER=0` disables opening the browser automatically.

## How it works

1. Upload a photo of the whole page with 12 diagrams (PNG, JPG, HEIC).
2. The app finds the 12 grids, reads the dots and recognises the scale from the title (OCR), the dot layout and the colours.
3. Pick the scale for the output chart: the one from the photo or any other.
4. Download a PNG or PDF in A4 at 300 dpi. "All scales (ZIP)" downloads every scale at once.

To regenerate the charts in `charts/` without starting the server:

```bash
.venv/bin/python generate_all.py charts
```

## Charts

All eleven charts are in [`charts/`](charts) as A4 PNG and PDF, ready to print. Click a chart for the full-size image.

<table>
<tr>
<td align="center"><a href="charts/ionian-12-positions-A4.png"><img src="docs/charts/ionian.png" alt="Ionian chart" width="260"></a><br><b>Ionian</b><br><code>1 2 3 4 5 6 7</code><br><a href="charts/ionian-12-positions-A4.png">PNG</a> · <a href="charts/ionian-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/dorian-12-positions-A4.png"><img src="docs/charts/dorian.png" alt="Dorian chart" width="260"></a><br><b>Dorian</b><br><code>1 2 b3 4 5 6 b7</code><br><a href="charts/dorian-12-positions-A4.png">PNG</a> · <a href="charts/dorian-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/phrygian-12-positions-A4.png"><img src="docs/charts/phrygian.png" alt="Phrygian chart" width="260"></a><br><b>Phrygian</b><br><code>1 b2 b3 4 5 b6 b7</code><br><a href="charts/phrygian-12-positions-A4.png">PNG</a> · <a href="charts/phrygian-12-positions-A4.pdf">PDF</a></td>
</tr>
<tr>
<td align="center"><a href="charts/lydian-12-positions-A4.png"><img src="docs/charts/lydian.png" alt="Lydian chart" width="260"></a><br><b>Lydian</b><br><code>1 2 3 #4 5 6 7</code><br><a href="charts/lydian-12-positions-A4.png">PNG</a> · <a href="charts/lydian-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/mixolydian-12-positions-A4.png"><img src="docs/charts/mixolydian.png" alt="Mixolydian chart" width="260"></a><br><b>Mixolydian</b><br><code>1 2 3 4 5 6 b7</code><br><a href="charts/mixolydian-12-positions-A4.png">PNG</a> · <a href="charts/mixolydian-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/aeolian-12-positions-A4.png"><img src="docs/charts/aeolian.png" alt="Aeolian chart" width="260"></a><br><b>Aeolian</b><br><code>1 2 b3 4 5 b6 b7</code><br><a href="charts/aeolian-12-positions-A4.png">PNG</a> · <a href="charts/aeolian-12-positions-A4.pdf">PDF</a></td>
</tr>
<tr>
<td align="center"><a href="charts/locrian-12-positions-A4.png"><img src="docs/charts/locrian.png" alt="Locrian chart" width="260"></a><br><b>Locrian</b><br><code>1 b2 b3 4 b5 b6 b7</code><br><a href="charts/locrian-12-positions-A4.png">PNG</a> · <a href="charts/locrian-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/harmonic-minor-12-positions-A4.png"><img src="docs/charts/harmonic-minor.png" alt="Harmonic Minor chart" width="260"></a><br><b>Harmonic Minor</b><br><code>1 2 b3 4 5 b6 7</code><br><a href="charts/harmonic-minor-12-positions-A4.png">PNG</a> · <a href="charts/harmonic-minor-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/major-pentatonic-12-positions-A4.png"><img src="docs/charts/major-pentatonic.png" alt="Major Pentatonic chart" width="260"></a><br><b>Major Pentatonic</b><br><code>1 2 3 5 6</code><br><a href="charts/major-pentatonic-12-positions-A4.png">PNG</a> · <a href="charts/major-pentatonic-12-positions-A4.pdf">PDF</a></td>
</tr>
<tr>
<td align="center"><a href="charts/minor-pentatonic-12-positions-A4.png"><img src="docs/charts/minor-pentatonic.png" alt="Minor Pentatonic chart" width="260"></a><br><b>Minor Pentatonic</b><br><code>1 b3 4 5 b7</code><br><a href="charts/minor-pentatonic-12-positions-A4.png">PNG</a> · <a href="charts/minor-pentatonic-12-positions-A4.pdf">PDF</a></td>
<td align="center"><a href="charts/diminished-12-positions-A4.png"><img src="docs/charts/diminished.png" alt="Diminished chart" width="260"></a><br><b>Diminished</b><br><code>1 2 b3 4 b5 b6 6 7</code><br><a href="charts/diminished-12-positions-A4.png">PNG</a> · <a href="charts/diminished-12-positions-A4.pdf">PDF</a></td>
</tr>
</table>

## Chart model

Every diagram shows the same six-fret window in a different key: position `n+1` is the same scale moved one fret down. Strings run left to right E A D G B e. The first and last rows (grey) are the frets next to the position; notes in those rows are left out when the same pitch already appears on a neighbouring string inside the white part of the diagram.

Colours mark scale degrees: 1 red, 2 orange, 3 yellow, 4 green, 5 light blue, 6 dark blue, 7 purple. A lowered or raised degree carries a `b` or `#` on its dot.

The modes of the major scale (Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian) share identical shapes and differ only in which note is the first degree. Harmonic Minor and Minor Pentatonic use the Aeolian root; Major Pentatonic and Diminished use the Ionian root.

Scales are defined in `converter/scales.py`; adding a scale takes one entry in `SCALES`.

## Photo recognition limits

- The photo has to show the whole page: 4 columns of 3 diagrams, reasonably straight and filling the frame.
- A faded photo of a mode without a readable title cannot be assigned to one scale, because the shapes are shared; the scale is then picked from the list.
- A chart that matches no known scale can be reproduced dot for dot with the colours read from the photo.

## Tests

```bash
.venv/bin/python -m pytest
```
