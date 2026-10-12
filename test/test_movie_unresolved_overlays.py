"""Test that overlays requested by a MOVIE, but not built by any plugin, are reported.

Two jobs: expose a bug that exists today (the test asserts the intended behaviour, so it FAILS until the bug is
fixed) and guard against regression once it is fixed.
"""
import configparser
import logging

from fileops.export._param_override import ParameterOverride
from movierender.plugins.fileops import MovieHeaderReaderPlugin


class _StubImage:
    frames = list(range(5))
    channels = [0, 1]
    zstacks = [0]
    series = 0
    n_frames = 5
    n_channels = 2
    n_zstacks = 1
    um_per_z = 1.0
    um_per_pix = 1.0
    pix_per_um = 1.0
    width = height = 64
    time_interval = 1.0
    timestamps = []


CFG_TEXT = """
[DATA]
image = data.tif

[MOVIE-1]
title = t
fps = 1
filename = out
overlays = [wall_001]

[OVERLAY-01]
id = wall_001
type = a_type_no_installed_plugin_handles
file = wall_001.csv
"""


def test_overlay_without_matching_plugin_is_reported(tmp_path, caplog):
    """A movie that lists an overlay id no plugin can build must log a warning (or raise) naming that id.

    Scenario: `[MOVIE-1] overlays = [wall_001]` and an `[OVERLAY-01] id = wall_001` whose `type` has no
    registered plugin (e.g. `type = compartment` when compartment-gui is not installed in the active venv).
    Symptom: the movie renders without the overlay, and nothing is logged or raised, so a missing
    plugin/typo looks identical to "nothing to draw".
    Cause: MovieHeaderReaderPlugin.process() builds the overlay list by filtering the available overlays on the
    requested ids; ids with no match are dropped without a message.
    Guards: a requested overlay can never disappear silently.
    """
    cfg = configparser.ConfigParser()
    cfg.read_string(CFG_TEXT)
    img = _StubImage()
    plugin = MovieHeaderReaderPlugin(tmp_path / "cfg.cfg", cfg=cfg, img_file=img,
                                     param_override=ParameterOverride(img), roi=None, defaults_file=None)
    assert plugin.has_valid_header()

    with caplog.at_level(logging.WARNING):
        movies = plugin.process()
    assert len(movies[0].overlays) == 0
    assert any("wall_001" in r.getMessage() for r in caplog.records), \
        "overlay 'wall_001' was requested by the movie but silently dropped"


CFG_MATCHED = """
[DATA]
image = data.tif

[OVERLAY-01]
id = arr_1
type = arrow
xy = (0, 0)
length = 1
angle = 0
color = yellow

[MOVIE-1]
title = t
fps = 1
filename = out
overlays = [arr_1]
"""


def test_matching_overlay_is_resolved_without_warning(tmp_path, caplog):
    """A requested overlay id that matches a plugin overlay must be resolved and not warned about."""
    cfg = configparser.ConfigParser()
    cfg.read_string(CFG_MATCHED)
    img = _StubImage()
    plugin = MovieHeaderReaderPlugin(tmp_path / "cfg.cfg", cfg=cfg, img_file=img,
                                     param_override=ParameterOverride(img), roi=None, defaults_file=None)
    assert plugin.has_valid_header()

    with caplog.at_level(logging.WARNING):
        movies = plugin.process()
    assert [o.overlay_id for o in movies[0].overlays] == ["arr_1"]
    assert not any("does not match any" in r.getMessage() for r in caplog.records), \
        "resolved overlays must not be reported as unmatched"
