"""Writes every scale chart as A4 PNG and PDF into the given folder (default: wykresy/)."""

import sys
from pathlib import Path

from converter.render import render_chart, to_pdf, to_png
from converter.scales import SCALES


def main(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for scale in SCALES.values():
        image = render_chart(scale)
        stem = scale.name.lower().replace(" ", "-") + "-12-pozycji-A4"
        (target / f"{stem}.png").write_bytes(to_png(image))
        (target / f"{stem}.pdf").write_bytes(to_pdf(image))
        print(f"{scale.name}: {scale.formula}")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("wykresy"))
