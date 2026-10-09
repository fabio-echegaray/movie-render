"""Tests that per-channel settings given in a [MOVIE]/[PANEL] section reach the rendered pixels.

Each test has two jobs: expose a bug that exists today (it asserts the intended behaviour, so it FAILS until the
bug is fixed) and guard against regression once it is fixed.
"""
from types import SimpleNamespace

import numpy as np
from movierender.layouts._ch_config import channel_configuration
from movierender.render.pipelines import CompositeRGBImage


class _StubImage:
    width = height = 8

    def z_projection(self, frame, channel, z_subset=None, projection="max"):
        img = np.linspace(0.05, 0.95, 64).reshape(8, 8)
        return SimpleNamespace(image=img)


def _render(**overrides):
    params = {0: {"name": "ch", "color": "white", **overrides}}
    pipe = CompositeRGBImage(ax=None, zstack=[0, 1], zstack_fn="max", channeldict=channel_configuration(params))
    pipe._renderer = SimpleNamespace(image=_StubImage(), frame=0)
    return pipe(frame=0)


def test_section_gamma_override_changes_rendered_image():
    """Gamma set for a channel in a section must change the pixels CompositeRGBImage produces.

    Scenario: a section sets `channel_1_gamma_value = 4` (with gain 1.0); the same image is rendered with and
    without that channel configuration.
    Symptom: the two renders are identical, so the override has no visible effect; it only shows up in the
    parsed parameters.
    Cause: rescale/gamma are applied once, at image load, by a RescaleProcessor built from the [DATA] and
    [CHANNEL-NN] values (fileops config_data_section.py). Section overrides are parsed later and the render
    pipeline only reads `color` and `intensity` from them.
    Guards: whichever way the fix applies gamma (at render time, or per-section processors), a gamma in the
    channel configuration must keep changing the output.
    """
    plain = _render()
    gamma = _render(gamma_value=4.0, gamma_gain=1.0)
    assert not np.allclose(plain, gamma)
