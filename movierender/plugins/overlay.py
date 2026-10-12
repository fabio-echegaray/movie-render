from __future__ import annotations

from typing import TYPE_CHECKING

from fileops.plugins.base_plugin import BaseFileOpsPlugin

if TYPE_CHECKING:
    from movierender.overlays.overlay import Overlay


class OverlayPlugin(BaseFileOpsPlugin):
    _ovl: Overlay

    def __init__(self, *args, **kwargs):
        super().__init__()

        self._args = args
        self._kwargs = kwargs
        self.overlay_id = kwargs.get("overlay_id")

    @property
    def overlay(self):
        return self._clz(*self._args, **self._kwargs)

    @property
    def configuration(self):
        return {'args': self._args, 'kwargs': self._kwargs}
