import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fileops.export.config import read_config


class _StubImage:
    frames = list(range(5))
    channels = [0, 1]
    zstacks = [0, 1]
    series = 0
    n_frames = 5
    n_channels = 2
    n_zstacks = 2
    um_per_z = 1.0
    pix_per_um = 1.0
    width = 100
    height = 100
    time_interval = 1.0
    timestamps = []
    image_path = "data.tif"
    base_path = Path(".")

    def add_processor(self, *args, **kwargs):
        pass


CFG_TEXT = """
[DATA]
image = data.tif
frame = all
channel = all

[CHANNEL-1]
name = cell-specific

[MOVIE-1]
title = Test Movie
fps = 10
filename = my_movie
layout = twoch
"""

DEFAULTS_TEXT = """
[DEFAULT]
rescale = yes

[COPYRIGHT]
author = Jane Doe
license = MIT

[CHANNEL-1]
name = 60x GFP
color = green
"""


class TestMovieDefaults(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.img_path = self.tmp / "data.tif"
        self.img_path.write_bytes(b"stub")
        self.cfg_path = self.tmp / "movie.cfg"
        self.cfg_path.write_text(CFG_TEXT)
        self.defaults_path = self.tmp / "defaults.cfg"
        self.defaults_path.write_text(DEFAULTS_TEXT)

    @patch("fileops.export.config_data_section.load_image_file", return_value=_StubImage())
    def test_copyright_and_channels_reach_config_movie(self, mock_load):
        exp = read_config(self.cfg_path, defaults_file=self.defaults_path)

        self.assertEqual(exp.copyright.author, "Jane Doe")
        self.assertEqual(exp.copyright.license, "MIT")

        mov = exp.movies[0]
        # the movie carries the defaults-file copyright so the renderer can embed it
        self.assertIsNotNone(mov.copyright)
        self.assertEqual(mov.copyright.author, "Jane Doe")

        # [DEFAULT]-inherited channel attributes (rescale) must still reach the
        # channels — the image-level RescaleProcessor reads them per channel —
        # while inert image-level flags do not leak into the channel definition
        ch = mov.channel_render_parameters[0]
        self.assertEqual(ch["name"], "cell-specific")
        self.assertIn("rescale", ch)

    @patch("fileops.export.config_data_section.load_image_file", return_value=_StubImage())
    def test_movie_copyright_is_none_without_defaults(self, mock_load):
        exp = read_config(self.cfg_path)

        self.assertIsNone(exp.copyright)
        self.assertIsNone(exp.movies[0].copyright)


if __name__ == '__main__':
    unittest.main()
