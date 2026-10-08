from fileops.image import ImageFile


def roi_pixel_box(roi, img_shape):
    """Return clamped pixel crop bounds ``(y0, y1, x0, x1)`` for an image of
    shape ``img_shape``, truncated to the intersection with the image."""
    height, width = img_shape[:2]
    y0 = max(0, int(roi.top))
    y1 = min(height, int(roi.bottom))
    x0 = max(0, int(roi.left))
    x1 = min(width, int(roi.right))
    return y0, y1, x0, x1


def crop_extent(extent, roi, img_shape, origin):
    """Return the ``imshow`` extent for an array sliced to the ``roi`` pixels.

    ``img`` rendered with this extent must be the array
    ``img[y0:y1, x0:x1]`` obtained with :func:`roi_pixel_box`, displayed with
    the same ``origin`` and the full-image ``extent``."""
    y0, y1, x0, x1 = roi_pixel_box(roi, img_shape)
    height, width = img_shape[:2]
    left, right, bottom, top = extent
    x_left = left + x0 * (right - left) / width
    x_right = left + x1 * (right - left) / width
    if origin == 'upper':
        y_top = top - y0 * (top - bottom) / height
        y_bottom = top - y1 * (top - bottom) / height
    else:
        y_bottom = bottom + y0 * (top - bottom) / height
        y_top = bottom + y1 * (top - bottom) / height
    return (x_left, x_right, y_bottom, y_top)


class PixelTools:
    def __init__(self, cimg: ImageFile, roi=None):
        self.um_per_pix = cimg.um_per_pix
        self._roi = roi
        if roi is None:
            self._px_x0 = self._px_y0 = 0
            self.width = cimg.width
            self.height = cimg.height
        else:
            y0, y1, x0, x1 = roi_pixel_box(roi, (cimg.height, cimg.width))
            self._px_y0, self._px_x0 = y0, x0
            self.width = x1 - x0
            self.height = y1 - y0

    def xy_ratio_to_pixels(self, x, y):
        if not (0 <= x <= 1):
            raise ValueError("x is not in expected range [0, 1].")
        if not (0 <= y <= 1):
            raise ValueError("y is not in expected range [0, 1].")
        return self._px_x0 + x * self.width, self._px_y0 + y * self.height

    def xy_ratio_to_um(self, x, y):
        if not (0 <= x <= 1):
            raise ValueError("x is not in expected range [0, 1].")
        if not (0 <= y <= 1):
            raise ValueError("y is not in expected range [0, 1].")
        px_x = self._px_x0 + x * self.width
        px_y = self._px_y0 + y * self.height
        return px_x * self.um_per_pix, px_y * self.um_per_pix