from converter.scales import GREY_ROWS, SCALES, chart_grids, occupancy


def labels(grid_row):
    return [cell.label if cell else None for cell in grid_row]


def test_ionian_position_one_matches_the_reference_chart():
    grid = chart_grids(SCALES["ionian"])[0]
    assert labels(grid[0]) == ["1", "4", None, None, None, "1"]
    assert labels(grid[1]) == [None, None, "7", "3", None, None]
    assert labels(grid[2]) == ["2", "5", "1", "4", "6", "2"]
    assert labels(grid[3]) == [None] * 6
    assert labels(grid[4]) == ["3", "6", "2", "5", "7", "3"]
    assert labels(grid[5]) == ["4", None, None, None, "1", "4"]


def test_modes_reuse_the_ionian_shapes():
    ionian = occupancy(SCALES["ionian"])
    for key in ("dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"):
        assert occupancy(SCALES[key]) == ionian


def test_mode_relabelling_matches_the_photographed_charts():
    lydian = chart_grids(SCALES["lydian"])[0]
    assert labels(lydian[0]) == ["5", "1", None, None, None, "5"]
    assert labels(lydian[1]) == [None, None, "#4", "7", None, None]
    mixolydian = chart_grids(SCALES["mixolydian"])[0]
    assert labels(mixolydian[0]) == ["4", "b7", None, None, None, "4"]
    assert labels(mixolydian[5]) == ["b7", None, None, None, "4", "b7"]


def test_formulas():
    assert SCALES["dorian"].formula == "1 2 b3 4 5 6 b7"
    assert SCALES["phrygian"].formula == "1 b2 b3 4 5 b6 b7"
    assert SCALES["aeolian"].formula == "1 2 b3 4 5 b6 b7"
    assert SCALES["locrian"].formula == "1 b2 b3 4 b5 b6 b7"
    assert SCALES["harmonic_minor"].formula == "1 2 b3 4 5 b6 7"
    assert SCALES["major_pentatonic"].formula == "1 2 3 5 6"
    assert SCALES["minor_pentatonic"].formula == "1 b3 4 5 b7"
    assert SCALES["diminished_whole_half"].formula == "1 2 b3 4 b5 b6 bb7 7"
    assert SCALES["diminished_half_whole"].formula == "1 b2 #2 3 #4 5 6 b7"


def test_harmonic_minor_is_aeolian_with_a_raised_seventh():
    aeolian = chart_grids(SCALES["aeolian"])
    harmonic = chart_grids(SCALES["harmonic_minor"])
    white_rows = [row for row in range(6) if row not in GREY_ROWS]
    for position in range(12):
        for row in white_rows:
            for string in range(6):
                natural, raised = aeolian[position][row][string], harmonic[position][row][string]
                if natural and natural.label == "b7":
                    assert raised is None
                elif raised and raised.label == "7":
                    assert natural is None
                else:
                    assert natural == raised


def test_pentatonics_are_subsets_of_their_parent_scales():
    for pentatonic, parent in (("major_pentatonic", "ionian"), ("minor_pentatonic", "aeolian")):
        child_grids, parent_grids = chart_grids(SCALES[pentatonic]), chart_grids(SCALES[parent])
        for position in range(12):
            for row in range(6):
                for string in range(6):
                    cell = child_grids[position][row][string]
                    if cell is not None:
                        assert cell == parent_grids[position][row][string]


def test_every_position_shifts_the_scale_one_fret():
    for scale in SCALES.values():
        grids = chart_grids(scale)
        for position in range(11):
            # Rows 1..4 of a position reappear one row lower in the next position.
            for row in range(1, 4):
                assert grids[position][row] == grids[position + 1][row + 1]
