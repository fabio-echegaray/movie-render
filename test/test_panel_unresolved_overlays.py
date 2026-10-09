"""Test that overlays requested by a PANEL, but not built by any plugin, are reported.

Two jobs: expose a bug that exists today (the test asserts the intended behaviour, so it FAILS until the bug is
fixed) and guard against regression once it is fixed.
"""
import configparser
import logging

from fileops.export._param_override import ParameterOverride
from movierender.plugins.fileops import PanelHeaderReaderPlugin


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

[PANEL-1]
title = t
layout = time-array
filename = out.pdf
overlays = [wall_001]

[OVERLAY-01]
id = wall_001
type = a_type_no_installed_plugin_handles
file = wall_001.csv
"""


def test_overlay_without_matching_plugin_is_reported(tmp_path, caplog):
    """A panel that lists an overlay id no plugin can build must log a warning (or raise) naming that id.

    Scenario: `[PANEL-1] overlays = [wall_001]` and an `[OVERLAY-01] id = wall_001` whose `type` has no
    registered plugin (e.g. `type = compartment` when compartment-gui is not installed in the active venv).
    Symptom: the panel renders without the overlay, and nothing is logged or raised, so a missing
    plugin/typo looks identical to "nothing to draw".
    Cause: PanelHeaderReaderPlugin.process() builds `overlay_objs` by filtering the available overlays on the
    requested ids; ids with no match are dropped without a message.
    Guards: a requested overlay can never disappear silently.
    """
    cfg = configparser.ConfigParser()
    cfg.read_string(CFG_TEXT)
    img = _StubImage()
    plugin = PanelHeaderReaderPlugin(tmp_path / "cfg.cfg", cfg=cfg, img_file=img,
                                     param_override=ParameterOverride(img), roi=None, defaults_file=None)
    assert plugin.has_valid_header()

    with caplog.at_level(logging.WARNING):
        panels = plugin.process()
    assert len(panels[0].overlays) == 0
    assert any("wall_001" in r.getMessage() for r in caplog.records), \
        "overlay 'wall_001' was requested by the panel but silently dropped"
