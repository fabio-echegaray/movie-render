"""Test Arrow overlay functionality."""


class TestArrowClass:
    """Test Arrow class existence and basic behavior."""

    def test_arrow_class_exists(self):
        from movierender.overlays._arrow import Arrow
        assert hasattr(Arrow, '__init__'), "Arrow should have __init__ method"

    def test_arrow_init_parameters(self):
        from movierender.overlays._arrow import Arrow
        arrow = Arrow(x=0, y=0)
        assert hasattr(arrow, 'overlay_id'), "Should have overlay_id attribute"
        assert hasattr(arrow, '_xy'), "Should have _xy attribute"
        assert hasattr(arrow, '_length'), "Should have _length attribute"

    def test_arrow_init_with_colors(self):
        from movierender.overlays._arrow import Arrow
        arrow = Arrow(x=0, y=0, c="red")
        assert hasattr(arrow, '_c'), "Should have _c attribute for color"

    def test_arrow_init_with_frame(self):
        from movierender.overlays._arrow import Arrow
        arrow = Arrow(x=0, y=0, frame=5)
        assert hasattr(arrow, '_kwargs'), "Should have _kwargs attribute"

    def test_arrow_plot_method_exists(self):
        from movierender.overlays._arrow import Arrow
        arrow = Arrow(x=0, y=0)
        assert hasattr(arrow, 'plot'), "Arrow should have plot method"


class TestArrowOverlayPlugin:
    """Test ArrowOverlayPlugin inheritance."""

    def test_arrow_overlay_plugin_inherits(self):
        from movierender.overlays._arrow import ArrowOverlayPlugin
        from movierender.plugins.overlay import OverlayPlugin
        assert issubclass(ArrowOverlayPlugin, OverlayPlugin), \
            "ArrowOverlayPlugin should inherit from OverlayPlugin"
