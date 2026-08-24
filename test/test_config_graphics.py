"""Test graphics configuration with property classes (Point 58).

This test demonstrates how to use the graphics property classes in configuration files.
The property classes (TextProperties, LineProperties, BackgroundProperties) allow
configuring overlay appearance parameters like font size, colors for timestamps,
text labels, scalebars, and histograms.
"""

from movierender.config import TextProperties, LineProperties, BackgroundProperties

from movierender.config._cfg_graphics import _parse_text_props, _parse_line_props, _parse_background_props


class TestTextProperties:
    """Test class for TextProperties."""

    def test_default_values(self):
        """Test that TextProperties has sensible defaults."""
        tp = TextProperties()
        assert tp.font_name == 'Arial'
        assert tp.font_size == 12
        assert tp.color == 'white'

    def test_custom_values(self):
        """Test that TextProperties accepts custom values."""
        tp = TextProperties(font_name='Helvetica', font_size=14, color='red')
        assert tp.font_name == 'Helvetica'
        assert tp.font_size == 14
        assert tp.color == 'red'

    def test_named_tuple_behavior(self):
        """Test that TextProperties behaves as a NamedTuple."""
        tp = TextProperties(font_size=10)
        assert tp[1] == 10  # font_size is index 1
        assert tp.font_size == 10


class TestLineProperties:
    """Test class for LineProperties."""

    def test_default_values(self):
        """Test that LineProperties has sensible defaults."""
        lp = LineProperties()
        assert lp.color == 'white'
        assert lp.width == 1.0

    def test_custom_values(self):
        """Test that LineProperties accepts custom values."""
        lp = LineProperties(color='yellow', width=3.0)
        assert lp.color == 'yellow'
        assert lp.width == 3.0


class TestBackgroundProperties:
    """Test class for BackgroundProperties."""

    def test_default_values(self):
        """Test that BackgroundProperties has sensible defaults."""
        bp = BackgroundProperties()
        assert bp.color == 'black'

    def test_custom_values(self):
        """Test that BackgroundProperties accepts custom values."""
        bp = BackgroundProperties(color='darkgray')
        assert bp.color == 'darkgray'


class TestConfigMovieGraphics:
    """Test class for ConfigMovie graphics fields."""

    def test_config_movie_has_graphics_fields(self):
        """Test that ConfigMovie has graphics property fields."""
        from movierender.config._cfg_movie import ConfigMovie

        assert hasattr(ConfigMovie, '_fields'), "ConfigMovie should be a NamedTuple"
        assert 'scalebar_text' in ConfigMovie._fields, "ConfigMovie should have scalebar_text"
        assert 'scalebar_line' in ConfigMovie._fields, "ConfigMovie should have scalebar_line"
        assert 'timestamp' in ConfigMovie._fields, "ConfigMovie should have timestamp"
        assert 'channel_label' in ConfigMovie._fields, "ConfigMovie should have channel_label"
        assert 'suptitle' in ConfigMovie._fields, "ConfigMovie should have suptitle"
        assert 'background' in ConfigMovie._fields, "ConfigMovie should have background"


class TestConfigPanelGraphics:
    """Test class for ConfigPanel graphics fields."""

    def test_config_panel_has_graphics_fields(self):
        """Test that ConfigPanel has graphics property fields."""
        from movierender.config._cfg_panel import ConfigPanel

        assert hasattr(ConfigPanel, '_fields'), "ConfigPanel should be a NamedTuple"
        assert 'scalebar_text' in ConfigPanel._fields, "ConfigPanel should have scalebar_text"
        assert 'scalebar_line' in ConfigPanel._fields, "ConfigPanel should have scalebar_line"
        assert 'timestamp' in ConfigPanel._fields, "ConfigPanel should have timestamp"
        assert 'background' in ConfigPanel._fields, "ConfigPanel should have background"


class TestParseTextProps:
    """Test class for _parse_text_props helper."""

    def test_parse_with_all_keys(self):
        """Test parsing with all keys present."""

        class MockSection:
            def get(self, key, default=None):
                data = {
                    'scalebar.font_name': 'Courier',
                    'scalebar.font_size': '10',
                    'scalebar.color':     'yellow'
                }
                return data.get(key, default)

        section = MockSection()
        result = _parse_text_props(section, 'scalebar')

        assert result.font_name == 'Courier'
        assert result.font_size == 10
        assert result.color == 'yellow'

    def test_parse_with_defaults(self):
        """Test parsing with no keys present (uses defaults)."""

        class MockSection:
            def get(self, key, default=None):
                return default

        section = MockSection()
        result = _parse_text_props(section, 'scalebar')

        assert result.font_name == TextProperties.font_name
        assert result.font_size == TextProperties.font_size
        assert result.color == TextProperties.color


class TestParseLineProps:
    """Test class for _parse_line_props helper."""

    def test_parse_with_all_keys(self):
        """Test parsing with all keys present."""

        class MockSection:
            def get(self, key, default=None):
                data = {
                    'scalebar.line_color': 'red',
                    'scalebar.line_width': '5'
                }
                return data.get(key, default)

        section = MockSection()
        result = _parse_line_props(section, 'scalebar')

        assert result.color == 'red'
        assert result.width == 5.0

    def test_parse_with_defaults(self):
        """Test parsing with no keys present (uses defaults)."""

        class MockSection:
            def get(self, key, default=None):
                return default

        section = MockSection()
        result = _parse_line_props(section, 'scalebar')

        assert result.color == LineProperties.color
        assert result.width == LineProperties.width


class TestParseBackgroundProps:
    """Test class for _parse_background_props helper."""

    def test_parse_with_key(self):
        """Test parsing with key present."""

        class MockSection:
            def get(self, key, default=None):
                data = {'background.color': 'navy'}
                return data.get(key, default)

        section = MockSection()
        result = _parse_background_props(section)

        assert result.color == 'navy'

    def test_parse_with_default(self):
        """Test parsing with no key present (uses default)."""

        class MockSection:
            def get(self, key, default=None):
                return default

        section = MockSection()
        result = _parse_background_props(section)

        assert result.color == BackgroundProperties.color


class TestOverlayTextProps:
    """Test class for _parse_overlay_text_props helper."""

    def test_parse_with_all_keys(self):
        """Test parsing with all keys present."""

        class MockSection:
            def get(self, key, default=None):
                data = {
                    'font_name':  'Courier',
                    'font_size':  '16',
                    'font_color': 'cyan'
                }
                return data.get(key, default)

        section = MockSection()
        from movierender.config import _parse_overlay_text_props
        result = _parse_overlay_text_props(section)

        assert result.font_name == 'Courier'
        assert result.font_size == 16
        assert result.color == 'cyan'
