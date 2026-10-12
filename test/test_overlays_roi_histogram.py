import configparser
import types

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from movierender.overlays import ImageHistogram, ImagejROI
from movierender.overlays._roi import ImagejROIOverlayPlugin
from movierender.plugins.fileops._movie_header_reader import roi_overlays_for_ids


def _roi(left, top, right, bottom, t_position=None):
    roi = types.SimpleNamespace(left=left, top=top, right=right, bottom=bottom)
    if t_position is not None:
        roi.t_position = t_position
    return roi


def _cfg_with_roi(id="roi_001", header="ROI-01", frame=None):
    cfg = configparser.ConfigParser()
    cfg.add_section(header)
    cfg.set(header, "id", id)
    cfg.set(header, "geometry", "Square(54,35,100)")
    if frame is not None:
        cfg.set(header, "frame", str(frame))
    return cfg


class TestRoiOverlaysForIds:
    def test_matches_by_section_id(self):
        cfg = _cfg_with_roi(id="roi_001", header="ROI-01")
        roi_lst = [types.SimpleNamespace(header="ROI-01", geometry=_roi(4, -15, 105, 86))]
        ovls = roi_overlays_for_ids(cfg, roi_lst, ["roi_001"], um_per_pix=0.2217)
        assert len(ovls) == 1
        assert ovls[0].overlay_id == "roi_001"

    def test_matches_by_section_header(self):
        cfg = _cfg_with_roi(id="roi_001", header="ROI-01")
        roi_lst = [types.SimpleNamespace(header="ROI-01", geometry=_roi(4, -15, 105, 86))]
        ovls = roi_overlays_for_ids(cfg, roi_lst, ["ROI-01"])
        assert len(ovls) == 1

    def test_no_match_returns_empty(self):
        cfg = _cfg_with_roi(id="roi_001", header="ROI-01")
        roi_lst = [types.SimpleNamespace(header="ROI-01", geometry=_roi(4, -15, 105, 86))]
        assert roi_overlays_for_ids(cfg, roi_lst, ["other_roi"]) == []

    def test_passes_um_per_pix_into_overlay(self):
        cfg = _cfg_with_roi(id="roi_001", header="ROI-01")
        roi_lst = [types.SimpleNamespace(header="ROI-01", geometry=_roi(4, -15, 105, 86))]
        ovls = roi_overlays_for_ids(cfg, roi_lst, ["roi_001"], um_per_pix=0.5)
        assert ovls[0]._kwargs.get("um_per_pix") == 0.5


class TestImagejROI:
    def test_single_geometry_is_normalized_to_list(self):
        ovl = ImagejROI(_roi(4, -15, 105, 86), um_per_pix=1.0)
        assert isinstance(ovl.roi_list, list) and len(ovl.roi_list) == 1

    def test_plot_static_roi_draws_rectangle(self):
        from matplotlib import patches as mpatches

        fig, ax = plt.subplots()
        ovl = ImagejROI(_roi(4, -15, 105, 86), um_per_pix=0.2217, overlay_id="roi_001")
        ovl.plot(ax=ax, frame=5)
        assert len(ax.patches) == 1
        assert isinstance(ax.patches[0], mpatches.Rectangle)

    def test_plot_skips_mismatched_following_roi(self):
        fig, ax = plt.subplots()
        following = _roi(4, -15, 105, 86, t_position=3)
        ovl = ImagejROI([following], um_per_pix=0.2217)
        ovl.plot(ax=ax, frame=5)
        assert len(ax.patches) == 0

    def test_plot_draws_following_roi_on_matching_frame(self):
        fig, ax = plt.subplots()
        following = _roi(4, -15, 105, 86, t_position=3)
        ovl = ImagejROI([following], um_per_pix=0.2217)
        ovl.plot(ax=ax, frame=3)
        assert len(ax.patches) == 1

    def test_static_roi_survives_default_t_position_0(self):
        # roifile gives a static geometry t_position == 0 by default, which
        # must not confine it to frame 0: static overlays draw on every frame.
        cfg = _cfg_with_roi(id="roi_001", header="ROI-01")
        roi_lst = [types.SimpleNamespace(header="ROI-01", geometry=_roi(4, -15, 105, 86, t_position=0))]
        ovls = roi_overlays_for_ids(cfg, roi_lst, ["roi_001"], um_per_pix=0.2217)
        assert len(ovls) == 1
        assert ovls[0].overlay.roi_list[0].t_position is None
        for frame in (0, 5, 15):
            fig, ax = plt.subplots()
            ovls[0].overlay.plot(ax=ax, frame=frame)
            assert len(ax.patches) == 1

    def test_frame_key_limits_static_roi_to_that_frame(self):
        cfg = _cfg_with_roi(id="roi_001", header="ROI-01", frame=10)
        roi_lst = [types.SimpleNamespace(header="ROI-01", geometry=_roi(4, -15, 105, 86, t_position=0))]
        ovls = roi_overlays_for_ids(cfg, roi_lst, ["roi_001"], um_per_pix=0.2217)
        assert ovls[0].overlay.roi_list[0].t_position == 10
        fig, ax = plt.subplots()
        ovls[0].overlay.plot(ax=ax, frame=10)
        assert len(ax.patches) == 1
        for frame in (0, 5, 15):
            fig, ax = plt.subplots()
            ovls[0].overlay.plot(ax=ax, frame=frame)
            assert len(ax.patches) == 0

    def test_following_roi_positions_are_preserved(self):
        following = [_roi(4, -15, 105, 86, t_position=0), _roi(104, -15, 205, 86, t_position=6)]
        ovl = ImagejROI(following, um_per_pix=0.2217)
        assert [r.t_position for r in ovl.roi_list] == [0, 6]

    def test_plugin_overlay_constructs_imagej_roi(self):
        plugin = ImagejROIOverlayPlugin([_roi(4, -15, 105, 86)], overlay_id="roi_001", um_per_pix=0.1)
        assert plugin.overlay_id == "roi_001"
        assert isinstance(plugin.overlay, ImagejROI)


class TestImageHistogramArray:
    def test_plot_accepts_grayscale(self):
        fig, ax = plt.subplots()
        hst = ImageHistogram(ax=ax, bins=50)
        hst.plot(np.zeros((512, 512)))

    def test_plot_accepts_rgb_composite(self):
        fig, ax = plt.subplots()
        hst = ImageHistogram(ax=ax, bins=4)
        hst.plot(np.full((8, 8, 3), 0.5))

    def test_plot_adds_inset_axes(self):
        fig, ax = plt.subplots()
        hst = ImageHistogram(ax=ax, bins=4)
        hst.plot(np.random.rand(64, 64))
        assert len(ax.child_axes) == 1