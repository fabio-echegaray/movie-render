from movierender.render.movie import MovieRenderer


class Overlay(object):
    def __init__(self, **kwargs):
        self.layers = [self]
        self._kwargs = kwargs
        self._renderer = None

    def __radd__(self, ovrl):
        if isinstance(ovrl, MovieRenderer):
            ovrl.layers += self.layers
            self._renderer = ovrl
            return ovrl

        self.layers.append(ovrl)
        return self

    def plot(self, ax, **kwargs):
        pass
