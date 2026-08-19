"""Test point 55: Ensure all overlay types are properly exported from movierender.overlays."""


class TestOverlayExports:
    """Test that all overlay types are exported from movierender.overlays."""

    def test_position_exported(self):
        import movierender.overlays as overlays
        assert hasattr(overlays, 'Position'), "Position should be exported"

    def test_arrow_exported(self):
        import movierender.overlays as overlays
        assert hasattr(overlays, 'Arrow'), "Arrow should be exported"

    def test_treatment_exported(self):
        import movierender.overlays as overlays
        assert hasattr(overlays, 'Treatment'), "Treatment should be exported"

    def test_image_histogram_exported(self):
        import movierender.overlays as overlays
        assert hasattr(overlays, 'ImageHistogram'), "ImageHistogram should be exported"

    def test_scale_bar_exported(self):
        import movierender.overlays as overlays
        assert hasattr(overlays, 'ScaleBar'), "ScaleBar should be exported"

    def test_timestamp_exported(self):
        import movierender.overlays as overlays
        assert hasattr(overlays, 'Timestamp'), "Timestamp should be exported"


class TestPluginExports:
    """Test that OverlayPlugin is re-exported from movierender.plugins."""

    def test_overlay_plugin_exported(self):
        import movierender.plugins as plugins
        assert hasattr(plugins, 'OverlayPlugin'), "OverlayPlugin should be exported"
