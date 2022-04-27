from fileops.image import ImageFile


class PixelTools:
    def __init__(self, cimg: ImageFile):
        self.width = 0
        self.height = 0
        self.um_per_pix = 0
        for d in cimg.__dict__:
            self.__dict__.update({d: cimg.__dict__[d]})

    def xy_ratio_to_pixels(self, x, y):
        # nfo = self.info
        assert 0 <= x <= 1, "x is not in expected range."
        assert 0 <= y <= 1, "y is not in expected range."
        return x * self.width, y * self.height

    def xy_ratio_to_um(self, x, y):
        assert 0 <= x <= 1, "x is not in expected range."
        assert 0 <= y <= 1, "y is not in expected range."
        return x * self.width * self.um_per_pix, y * self.height * self.um_per_pix
