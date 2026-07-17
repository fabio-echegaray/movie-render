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
        if not (0 <= x <= 1):
            raise ValueError("x is not in expected range [0, 1].")
        if not (0 <= y <= 1):
            raise ValueError("y is not in expected range [0, 1].")
        return x * self.width, y * self.height

    def xy_ratio_to_um(self, x, y):
        if not (0 <= x <= 1):
            raise ValueError("x is not in expected range [0, 1].")
        if not (0 <= y <= 1):
            raise ValueError("y is not in expected range [0, 1].")
        return x * self.width * self.um_per_pix, y * self.height * self.um_per_pix
