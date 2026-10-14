import numpy as np
import pytest
from fileops.image.exceptions import FrameNotFoundError
from fileops.image.ops import ZProjection
from matplotlib import pyplot as plt
from unittest.mock import patch

from movierender.colorize import (
    DEFAULT_DEPTH_CMAP, depth_cmap, normalized_intensity, is_depth_projection,
    z_depth_rgb,
)


class TestIsDepthProjection:
    @pytest.mark.parametrize("value", ["depth", "all-depth", "code", "all-code",
                                       "DEPTH", "Depth", "all-Depth"])
    def test_recognises_depth_names(self, value):
        assert is_depth_projection(value)

    @pytest.mark.parametrize("value", ["max", "all-max", "mean", "sum", "depthy",
                                       3, None, ZProjection.MAX])
    def test_rejects_non_depth(self, value):
        assert not is_depth_projection(value)


class TestDepthCmap:
    def test_default_is_perceptually_uniform(self):
        assert DEFAULT_DEPTH_CMAP == 'plasma'

    def test_returns_rgb(self):
        field = np.zeros((8, 8))
        intensity = np.ones((8, 8))
        out = depth_cmap(field, intensity)
        assert out.shape == (8, 8, 3)

    def test_colours_follow_field(self):
        field = np.zeros((8, 8))
        field[0, 0] = 0.0
        field[7, 7] = 1.0
        out = depth_cmap(field, np.ones((8, 8)))
        plasma = plt.get_cmap('plasma')
        np.testing.assert_allclose(out[0, 0], plasma(0.0)[:3], atol=1e-9)
        np.testing.assert_allclose(out[7, 7], plasma(1.0)[:3], atol=1e-9)

    def test_intensity_scales_brightness(self):
        field = np.ones((8, 8))
        intensity = np.full((8, 8), 0.5)
        out = depth_cmap(field, intensity)
        expected = np.asarray(plt.get_cmap('plasma')(1.0)[:3]) * 0.5
        np.testing.assert_allclose(out, np.broadcast_to(expected, out.shape))

    def test_zero_intensity_is_black(self):
        out = depth_cmap(np.full((8, 8), 0.5), np.zeros((8, 8)))
        np.testing.assert_allclose(out, 0.0, atol=1e-12)

    def test_cmap_override(self):
        field = np.full((8, 8), 0.5)
        out_a = depth_cmap(field, np.ones((8, 8)), cmap_name='plasma')
        out_b = depth_cmap(field, np.ones((8, 8)), cmap_name='viridis')
        assert not np.allclose(out_a, out_b)

    def test_out_of_range_depth_is_clamped(self):
        field = np.array([[-1.0, 2.0]])
        out = depth_cmap(field, np.ones((1, 2)))
        plasma = plt.get_cmap('plasma')
        np.testing.assert_allclose(out[0, 0], plasma(0.0)[:3], atol=1e-9)
        np.testing.assert_allclose(out[0, 1], plasma(1.0)[:3], atol=1e-9)

    def test_unknown_colormap_raises(self):
        with pytest.raises(ValueError, match="depth-coding"):
            depth_cmap(np.zeros((2, 2)), np.ones((2, 2)), cmap_name='not-a-cmap')


class TestNormalizedIntensity:
    def test_unit_range(self):
        im = np.array([[1.0, 2.0], [3.0, 4.0]])
        np.testing.assert_allclose(normalized_intensity(im),
                                   np.array([[0.0, 1 / 3], [2 / 3, 1.0]]))

    def test_flat_map_is_zero(self):
        out = normalized_intensity(np.ones((3, 3)))
        np.testing.assert_allclose(out, 0.0)


class TestZDepthRGB:
    def test_combines_depth_and_intensity(self):
        # bottom-left pixel peaks at the bottom of the stack, top-right at the
        # top; brightness follows the max projection (1.0 vs 2.0 -> 0.5 vs 1.0)
        vol = np.zeros((4, 4, 4))
        vol[0, 0, 0] = 1.0
        vol[3, 3, 3] = 2.0

        with patch("movierender.colorize.z_volume", return_value=vol) as zvol:
            out = z_depth_rgb(object(), frame=0, channel=0, z_subset=[0, 1, 2, 3])
        zvol.assert_called_once()
        assert out.shape == (4, 4, 3)
        plasma = plt.get_cmap('plasma')
        np.testing.assert_allclose(out[3, 3], plasma(1.0)[:3], atol=1e-9)
        np.testing.assert_allclose(out[0, 0], np.asarray(plasma(0.0)[:3]) * 0.5, atol=1e-9)

    def test_honours_z_subset(self):
        vol = np.zeros((3, 2, 2))
        with patch("movierender.colorize.z_volume", return_value=vol) as zvol:
            z_depth_rgb(object(), frame=0, channel=0, z_subset=[1, 2, 3])
        assert zvol.call_args.kwargs['z_subset'] == [1, 2, 3]

    def test_whole_stack_when_z_subset_none(self):
        vol = np.zeros((3, 2, 2))
        with patch("movierender.colorize.z_volume", return_value=vol) as zvol:
            z_depth_rgb(object(), frame=5, channel=2)
        assert zvol.call_args.kwargs['z_subset'] is None
        assert zvol.call_args.kwargs['channel'] == 2
        assert zvol.call_args.kwargs['frame'] == 5

    def test_accepts_uint16_volume(self):
        # real microscopy planes are u16, not float
        vol = np.zeros((4, 4, 4), dtype=np.uint16)
        vol[0, 0, 0] = 50
        vol[3, 3, 3] = 100
        with patch("movierender.colorize.z_volume", return_value=vol):
            out = z_depth_rgb(object(), frame=0, channel=0, z_subset=[0, 1, 2, 3])
        assert out.shape == (4, 4, 3)
        assert out.dtype == np.float64
        plasma = plt.get_cmap('plasma')
        np.testing.assert_allclose(out[3, 3], plasma(1.0)[:3], atol=1e-9)
        np.testing.assert_allclose(out[0, 0], np.asarray(plasma(0.0)[:3]) * 0.5, atol=1e-9)

    def test_propagates_frame_not_found(self):
        with patch("movierender.colorize.z_volume",
                   side_effect=FrameNotFoundError("no stack at t=0 c=0")):
            with pytest.raises(FrameNotFoundError):
                z_depth_rgb(object(), frame=0, channel=0)