from movierender.layouts._ch_config import channel_configuration


class TestChannelConfiguration:
    def test_single_channel_basic(self):
        params = {
            0: {"name": "GFP", "color": "green", "intensity": 1.0}
        }
        result = channel_configuration(params)
        assert "GFP" in result
        assert result["GFP"]["id"] == 0
        assert result["GFP"]["color"] == "green"
        assert result["GFP"]["intensity"] == 1.0

    def test_multiple_channels(self):
        params = {
            0: {"name": "GFP", "color": "green", "intensity": 0.8},
            1: {"name": "RFP", "color": "red", "intensity": 1.0}
        }
        result = channel_configuration(params)
        assert len(result) == 2
        assert "GFP" in result
        assert "RFP" in result

    def test_color_strips_tuple_prefix(self):
        # When color is a tuple with >3 elements, strip the first element
        params = {
            0: {"name": "ch1", "color": (0.1, 0.2, 0.3, 1.0), "intensity": 1.0}
        }
        result = channel_configuration(params)
        assert result["ch1"]["color"] == (0.2, 0.3, 1.0)

    def test_color_tuple_three_elements_kept(self):
        params = {
            0: {"name": "ch1", "color": (0.1, 0.2, 0.3), "intensity": 1.0}
        }
        result = channel_configuration(params)
        assert result["ch1"]["color"] == (0.1, 0.2, 0.3)

    def test_intensity_default_when_missing(self):
        params = {
            0: {"name": "ch1", "color": "blue"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["intensity"] == 1.0

    def test_rescale_true_string(self):
        params = {
            0: {"name": "ch1", "color": "red", "rescale": "true"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["rescale"] is True

    def test_rescale_yes_string(self):
        params = {
            0: {"name": "ch1", "color": "red", "rescale": "yes"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["rescale"] is True

    def test_rescale_false_string(self):
        params = {
            0: {"name": "ch1", "color": "red", "rescale": "false"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["rescale"] is False

    def test_rescale_min_max(self):
        params = {
            0: {"name":        "ch1", "color": "red", "rescale": "true",
                "rescale_min": "100", "rescale_max": "2000"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["rescale_min"] == 100.0
        assert result["ch1"]["rescale_max"] == 2000.0

    def test_rescale_min_max_default_none(self):
        params = {
            0: {"name": "ch1", "color": "red", "rescale": "true"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["rescale_min"] is None
        assert result["ch1"]["rescale_max"] is None

    def test_gamma_values(self):
        params = {
            0: {"name":        "ch1", "color": "red",
                "gamma_value": "2.0", "gamma_gain": "0.5"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["gamma_value"] == 2.0
        assert result["ch1"]["gamma_gain"] == 0.5

    def test_gamma_defaults(self):
        params = {
            0: {"name": "ch1", "color": "red", "gamma_value": "1.5"}
        }
        result = channel_configuration(params)
        assert result["ch1"]["gamma_value"] == 1.5
        assert result["ch1"]["gamma_gain"] == 1.0

    def test_empty_params(self):
        result = channel_configuration({})
        assert result == {}

    def test_rescale_and_gamma_mutually_exclusive(self):
        # rescale key present takes precedence over gamma
        params = {
            0: {"name": "ch1", "color": "red", "rescale": "true", "gamma_value": "2.0"}
        }
        result = channel_configuration(params)
        assert "rescale" in result["ch1"]
        assert "gamma_value" not in result["ch1"]
