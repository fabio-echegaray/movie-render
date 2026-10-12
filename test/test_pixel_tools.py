import types

import pytest

from movierender.overlays.pixel_tools import PixelTools, crop_extent, roi_pixel_box


def _roi(left, top, right, bottom):
    return types.SimpleNamespace(left=left, top=top, right=right, bottom=bottom)


class TestRoiPixelBox:
    def test_in_image(self):
        roi = _roi(75, 75, 125, 125)
        assert roi_pixel_box(roi, (512, 512)) == (75, 125, 75, 125)

    def test_clamps_above_top_and_left(self):
        # Square(54, 35, 100) extends 15 px above the image top
        roi = _roi(4, -15, 105, 86)
        assert roi_pixel_box(roi, (512, 512)) == (0, 86, 4, 105)

    def test_clamps_below_and_right(self):
        roi = _roi(500, 500, 600, 600)
        assert roi_pixel_box(roi, (512, 512)) == (500, 512, 500, 512)

    def test_fully_outside_yields_no_crop(self):
        roi = _roi(-50, -50, -10, -10)
        y0, y1, x0, x1 = roi_pixel_box(roi, (512, 512))
        assert x1 <= x0 and y1 <= y0


class TestCropExtent:
    def test_panel_origin_upper(self):
        roi = _roi(75, 75, 125, 125)
        ext = crop_extent((0.0, 5.12, 5.12, 0.0), roi, (512, 512, 3), 'upper')
        assert ext == pytest.approx((0.75, 1.25, 1.25, 0.75))

    def test_movie_origin_lower(self):
        roi = _roi(75, 75, 125, 125)
        ext = crop_extent((0.0, 512.0, 0.0, 512.0), roi, (512, 512, 3), 'lower')
        assert ext == pytest.approx((75.0, 125.0, 75.0, 125.0))

    def test_movie_origin_upper(self):
        roi = _roi(75, 75, 125, 125)
        ext = crop_extent((0.0, 512.0, 0.0, 512.0), roi, (512, 512, 3), 'upper')
        assert ext == pytest.approx((75.0, 125.0, 387.0, 437.0))

    def test_full_image_returns_original_extent(self):
        roi = _roi(0, 0, 512, 512)
        ext = crop_extent((0.0, 5.12, 5.12, 0.0), roi, (512, 512, 3), 'upper')
        assert ext == pytest.approx((0.0, 5.12, 5.12, 0.0))

    def test_cropped_slice_maps_to_same_pixels(self):
        import numpy as np

        img = np.arange(512 * 512).reshape(512, 512)
        roi = _roi(75, 75, 125, 125)
        y0, y1, x0, x1 = roi_pixel_box(roi, img.shape)
        disp = img[y0:y1, x0:x1]
        assert disp.shape == (50, 50)
        assert disp[0, 0] == img[75, 75]
        assert disp[-1, -1] == img[124, 124]


class TestPixelTools:
    def _img(self, width=512, height=512, um_per_pix=0.01):
        return types.SimpleNamespace(width=width, height=height, um_per_pix=um_per_pix)

    def test_without_roi_uses_full_image(self):
        t = PixelTools(self._img())
        assert (t.width, t.height) == (512, 512)
        assert t.xy_ratio_to_um(1, 1) == (5.12, 5.12)
        assert t.xy_ratio_to_pixels(0.5, 0.5) == (256.0, 256.0)

    def test_with_roi_offsets_and_limits(self):
        t = PixelTools(self._img(), roi=_roi(75, 75, 125, 125))
        assert (t.width, t.height) == (50, 50)
        assert t.xy_ratio_to_um(0, 0) == (0.75, 0.75)
        assert t.xy_ratio_to_um(1, 1) == (1.25, 1.25)
        assert t.xy_ratio_to_pixels(0, 0) == (75.0, 75.0)
        assert t.xy_ratio_to_pixels(1, 1) == (125.0, 125.0)

    def test_ratio_out_of_range_raises(self):
        t = PixelTools(self._img())
        with pytest.raises(ValueError):
            t.xy_ratio_to_um(1.1, 0.5)
        with pytest.raises(ValueError):
            t.xy_ratio_to_um(0.5, -0.2)

    def test_with_roi_clamped_to_image(self):
        t = PixelTools(self._img(), roi=_roi(4, -15, 105, 86))
        assert (t.width, t.height) == (101, 86)
        assert t.xy_ratio_to_pixels(0, 0) == (4.0, 0.0)