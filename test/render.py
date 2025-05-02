from unittest import TestCase

from typer.testing import CliRunner

from movierender.scripts.render import app


class TestRender(TestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.runner = CliRunner()

    def test_render_file(self):
        command_name = "file"
        args = [command_name, "example_data/test.cfg"]

        result = self.runner.invoke(app, args)

        self.assertEqual(result.exit_code, 0)
