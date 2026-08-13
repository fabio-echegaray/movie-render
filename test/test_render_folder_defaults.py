import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import movierender.scripts._render_folder as rf


class TestRenderFolderDefaults(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def test_autodetect_defaults_file(self):
        (self.tmp / "defaults.cfg").write_text("[DEFAULT]\nfps = 15\n")
        cfg1 = self.tmp / "a.cfg"
        cfg1.write_text("[DATA]\n")
        sub = self.tmp / "sub"
        sub.mkdir()
        cfg2 = sub / "b.cfg"
        cfg2.write_text("[DATA]\n")

        mock_render = MagicMock(return_value=None)
        with patch.object(rf, "render_configuration_file_cmd", mock_render):
            n = rf.render_folder_cmd(self.tmp, overwrite_files=True)

        self.assertEqual(n, 2)
        calls = mock_render.call_args_list
        rendered_paths = [c[0][0] for c in calls]
        # defaults.cfg must not be rendered as a configuration file
        self.assertNotIn(self.tmp / "defaults.cfg", rendered_paths)
        self.assertEqual(len(rendered_paths), 2)
        # every configuration file receives the autodetected defaults file
        for c in calls:
            self.assertEqual(c[1]["defaults_file"], self.tmp / "defaults.cfg")

    def test_no_defaults_file(self):
        cfg1 = self.tmp / "a.cfg"
        cfg1.write_text("[DATA]\n")

        mock_render = MagicMock(return_value=None)
        with patch.object(rf, "render_configuration_file_cmd", mock_render):
            n = rf.render_folder_cmd(self.tmp, overwrite_files=True)

        self.assertEqual(n, 1)
        self.assertIsNone(mock_render.call_args_list[0][1]["defaults_file"])

    def test_explicit_defaults_file_is_excluded_from_render_list(self):
        cfg1 = self.tmp / "a.cfg"
        cfg1.write_text("[DATA]\n")
        defaults = self.tmp / "project_defaults.cfg"
        defaults.write_text("[DEFAULT]\nfps = 15\n")

        mock_render = MagicMock(return_value=None)
        with patch.object(rf, "render_configuration_file_cmd", mock_render):
            n = rf.render_folder_cmd(self.tmp, overwrite_files=True, defaults_file=defaults)

        self.assertEqual(n, 1)
        self.assertEqual(mock_render.call_args_list[0][1]["defaults_file"], defaults)


if __name__ == '__main__':
    unittest.main()
