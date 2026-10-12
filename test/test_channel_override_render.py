"""Tests that per-channel settings given in a [MOVIE]/[PANEL] section reach the rendered pixels.

Section-level ``gamma_*``/``rescale_*`` overrides are applied at image-load time,
not by the compositing pipeline: the renderers call
``configure_rescale_processor()`` before pulling frames, which reconfigures the
shared FileOps ``RescaleProcessor`` with the section's merged
``channel_render_parameters`` (``movierender/layouts/panel/_main.py`` and
``movierender/render/_sequential.py``). ``CompositeRGBImage`` only reads
``color``/``intensity``, so the override must be exercised through the loader.

Each test has two jobs: expose the bug (it asserts the intended behaviour, so it
fails until the section override reaches the loader) and guard against regression.
"""
import configparser

import numpy as np
from fileops.export._param_override import ParameterOverride
from fileops.export.config_channel_section import update_channel_config_with_section_overrides
from fileops.image.imagemeta import MetadataImage
from fileops.image.ops.rescale_proc import configure_rescale_processor


class _StubImage:
    frames = [0, 1, 2, 3]
    channels = [0]
    zstacks = [0]
    n_frames = 4
    n_channels = 1
    n_zstacks = 1


class _StubImageFile:
    """Minimal ImageFile surface used by ``configure_rescale_processor()``."""

    def __init__(self):
        self.processing_deque = []

    def add_processor(self, processor):
        self.processing_deque.append(processor)


def _section(text):
    cp = configparser.ConfigParser()
    cp.read_string(text)
    return cp[cp.sections()[0]]


def _render_section(section_body):
    """Resolve a section into channel_render_parameters, reconfigure the image-load
    RescaleProcessor with them, and return the pixels the loader would produce."""
    sec = _section(section_body)
    sec_po = update_channel_config_with_section_overrides(ParameterOverride(_StubImage()), sec)

    imf = _StubImageFile()
    configure_rescale_processor(imf, sec_po.channel_info)

    img = np.linspace(0.05, 0.95, 64, dtype=np.float64).reshape(8, 8)
    mdi = MetadataImage(reader="test", image=img, pix_per_um=1, um_per_pix=1,
                        time_interval=1, frame=0, channel=0, z=0,
                        width=8, height=8, timestamp=0, intensity_range=(0, 1))
    for processor in imf.processing_deque:
        mdi = processor.process(mdi)
    return mdi.image


def test_section_gamma_override_changes_rendered_image():
    """Gamma set for a channel in a section must change the pixels the loader produces.

    Scenario: a section sets `channel_1_gamma_value = 4` (gain defaults to 1.0);
    the same image is loaded with and without that section.
    Symptom: the two renders are identical, so the override has no visible effect;
    it only shows up in the parsed parameters.
    Guards: the section's gamma reaches the image-load RescaleProcessor, so the
    rendered pixels keep changing; a section without gamma adds no processor.
    """
    plain = _render_section("[PANEL]\n")
    gamma = _render_section("[PANEL]\nchannel_1_gamma_value = 4.0\n")
    assert not np.allclose(plain, gamma)
