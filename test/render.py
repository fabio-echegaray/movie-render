from unittest import TestCase

import fileops
from typer.testing import CliRunner

from movierender.scripts.render import app


class TestRender(TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.runner = CliRunner()

        # init shared variables used by FileOps
        fileops.init_shared_state()

    def test_render_movie_different_frames(self):
        command_name = "movie"

        args = [command_name, "example_data/test_frames_movie.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_movie_swap_channels(self):
        command_name = "movie"

        args = [command_name, "example_data/test_frames_movie_ch_swap.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_movie_rescale_intensity(self):
        command_name = "movie"

        args = [command_name, "example_data/test_ch_intensity_movie.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_movie_histogram_match_2D(self):
        command_name = "movie"

        args = [command_name, "example_data/test_ch_hist_match_movie.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_projection(self):
        command_name = "projection"

        args = [command_name, "example_data/test_frames_projection.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_panel(self):
        command_name = "panel"

        args = [command_name, "example_data/test_panels.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_overlays(self):
        command_name = "file"

        args = [command_name, "example_data/test_movie_panel_overlay.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_folder(self):
        command_name = "folder"

        args = [command_name, "example_data"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_file_rejects_directory(self):
        command_name = "file"

        args = [command_name, "test/example_data"]
        result = self.runner.invoke(app, args)
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("use 'movierender folder'", result.stderr)


if __name__ == "__main__":
    app()
