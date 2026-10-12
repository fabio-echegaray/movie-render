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


class TestMovieSizeAndCodec(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.img_path = self.tmp / "data.tif"
        self.img_path.write_bytes(b"stub")

    def _cfg(self, movie_extra=""):
        path = self.tmp / ("movie_%d.cfg" % len(movie_extra))
        path.write_text(
            CFG_TEXT.replace("[MOVIE-1]", "[MOVIE-1]\n" + movie_extra)
        )
        return path

    @patch("fileops.export.config_data_section.load_image_file", return_value=_StubImage())
    def test_defaults_are_current_values(self, mock_load):
        movie = read_config(self._cfg("")).movies[0]
        self.assertEqual(movie.max_width, 2880)
        self.assertEqual(movie.dpi, 326)
        self.assertEqual(movie.codec, "libx264")

    @patch("fileops.export.config_data_section.load_image_file", return_value=_StubImage())
    def test_size_and_codec_are_parsed(self, mock_load):
        movie = read_config(self._cfg(
            "max_width = 1920\n"
            "dpi = 150\n"
            "codec = H.265\n"
        )).movies[0]
        self.assertEqual(movie.max_width, 1920)
        self.assertEqual(movie.dpi, 150)
        self.assertEqual(movie.codec, "libx265")

    def test_resolve_movie_codec(self):
        from movierender.plugins.fileops._movie_header_reader import resolve_movie_codec
        self.assertEqual(resolve_movie_codec(""), "libx264")
        self.assertEqual(resolve_movie_codec("h264"), "libx264")
        self.assertEqual(resolve_movie_codec("H.264"), "libx264")
        self.assertEqual(resolve_movie_codec("libx264"), "libx264")
        self.assertEqual(resolve_movie_codec("H.265"), "libx265")
        self.assertEqual(resolve_movie_codec("hevc"), "libx265")
        self.assertEqual(resolve_movie_codec("libx265"), "libx265")
        self.assertEqual(resolve_movie_codec("libvpx"), "libvpx")


if __name__ == '__main__':
    unittest.main()
