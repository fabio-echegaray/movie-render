import configparser
from pathlib import Path

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
zstack_fn = max
"""


def _panel(cfg_text):
    cfg = configparser.ConfigParser()
    cfg.read_string(cfg_text)
    img = _StubImage()
    plugin = PanelHeaderReaderPlugin(Path("cfg.cfg"), cfg=cfg, img_file=img,
                                     param_override=ParameterOverride(img), roi=None,
                                     defaults_file=None)
    assert plugin.has_valid_header()
    return plugin.process()[0]


def test_zstack_cmap_default_is_perceptually_uniform():
    panel = _panel(CFG_TEXT)
    assert panel.zstack_cmap == "plasma"


def test_zstack_cmap_read_from_cfg():
    panel = _panel(CFG_TEXT.replace("[PANEL-1]", "[PANEL-1]\nzstack_cmap = viridis"))
    assert panel.zstack_cmap == "viridis"