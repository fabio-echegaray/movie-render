from unittest import TestCase

from typer.testing import CliRunner

from movierender.scripts.render import app


class TestRender(TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.runner = CliRunner()

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

    def test_render_panel(self):
        command_name = "panel"

        args = [command_name, "example_data/test_panels.cfg"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.exit_code, 0)

    def test_render_folder(self):
        command_name = "folder"

        args = [command_name, "example_data"]
        result = self.runner.invoke(app, args)
        self.assertEqual(result.return_value, 0)
        self.assertEqual(result.exit_code, 0)


if __name__ == "__main__":
    app()
