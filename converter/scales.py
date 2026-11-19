"""Scale definitions and the 12-position fretboard model.

Every chart shows the same six-fret window of the fretboard in 12 keys:
position p shifts the scale one fret down relative to position p-1. Modes of
the major scale reuse the Ionian shapes and only relabel the degrees, so each
scale stores the distance of its root from the Ionian root.
"""

from dataclasses import dataclass

STRINGS = 6
ROWS = 6
POSITIONS = 12

# Semitones above the low E string, modulo 12, for strings E A D G B e.
STRING_OFFSETS = (0, 5, 10, 3, 7, 0)
G_STRING = 3
B_STRING = 4

GREY_ROWS = (0, ROWS - 1)


@dataclass(frozen=True)
class Degree:
    number: int
    accidental: str = ""

    @property
    def label(self) -> str:
        return f"{self.accidental}{self.number}"


@dataclass(frozen=True)
class Scale:
    key: str
    name: str
    subtitle: str
    # semitone above the scale root -> degree
    degrees: dict
    # semitones from the Ionian root of the shared shapes up to this scale's root
    root_offset: int

    @property
    def formula(self) -> str:
        return " ".join(self.degrees[s].label for s in sorted(self.degrees))


def _degrees(spec: str) -> dict:
    natural = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
    result = {}
    for token in spec.split():
        accidental = token[:-1]
        number = int(token[-1])
        shift = {"": 0, "b": -1, "#": 1, "bb": -2}[accidental]
        result[(natural[number] + shift) % 12] = Degree(number, accidental)
    return result


def _scale(key, name, subtitle, spec, root_offset):
    return Scale(key, name, subtitle, _degrees(spec), root_offset)


SCALES = {
    s.key: s
    for s in (
        _scale("ionian", "Ionian", "MAJOR DIATONIC", "1 2 3 4 5 6 7", 0),
        _scale("dorian", "Dorian", "MINOR MODE", "1 2 b3 4 5 6 b7", 2),
        _scale("phrygian", "Phrygian", "MINOR MODE", "1 b2 b3 4 5 b6 b7", 4),
        _scale("lydian", "Lydian", "MAJOR MODE", "1 2 3 #4 5 6 7", 5),
        _scale("mixolydian", "Mixolydian", "DOMINANT MODE", "1 2 3 4 5 6 b7", 7),
        _scale("aeolian", "Aeolian", "NATURAL MINOR", "1 2 b3 4 5 b6 b7", 9),
        _scale("locrian", "Locrian", "HALF-DIMINISHED MODE", "1 b2 b3 4 b5 b6 b7", 11),
        _scale("harmonic_minor", "Harmonic Minor", "MINOR", "1 2 b3 4 5 b6 7", 9),
        _scale("major_pentatonic", "Major Pentatonic", "PENTATONIC", "1 2 3 5 6", 0),
        _scale("minor_pentatonic", "Minor Pentatonic", "PENTATONIC", "1 b3 4 5 b7", 9),
        _scale("diminished", "Diminished", "WHOLE-HALF", "1 2 b3 4 b5 b6 6 7", 0),
    )
}


def _is_hidden_duplicate(row: int, string: int) -> bool:
    """Grey-row notes that repeat a pitch already inside the white rows.

    Only the major third between the G and B strings brings such a duplicate
    into the four white rows; the source charts leave those dots out.
    """
    return (row == 0 and string == B_STRING) or (row == ROWS - 1 and string == G_STRING)


def position_grid(scale: Scale, position: int) -> list:
    """Return ROWS x STRINGS cells holding a Degree or None for position 1..12."""
    grid = []
    for row in range(ROWS):
        cells = []
        for string in range(STRINGS):
            above_ionian_root = (1 - position + row + STRING_OFFSETS[string]) % 12
            degree = scale.degrees.get((above_ionian_root - scale.root_offset) % 12)
            if degree is not None and _is_hidden_duplicate(row, string):
                degree = None
            cells.append(degree)
        grid.append(cells)
    return grid


def chart_grids(scale: Scale) -> list:
    return [position_grid(scale, p) for p in range(1, POSITIONS + 1)]


def occupancy(scale: Scale) -> list:
    """Boolean dot layout of the whole chart, used to recognise photographed charts."""
    return [[[cell is not None for cell in row] for row in grid] for grid in chart_grids(scale)]
