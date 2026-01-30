from fileops.plugins.base_plugin import BaseFileOpsPlugin

from movierender.overlays import Overlay


class OverlayPlugin(BaseFileOpsPlugin):
    _ovl: Overlay

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._args = args
        self._kwargs = kwargs

    @property
    def overlay(self):
        if self._ovl is None:
            raise NotImplementedError
        return self._ovl

    @property
    def configuration(self):
        return {'args': self._args, 'kwargs': self._kwargs}
