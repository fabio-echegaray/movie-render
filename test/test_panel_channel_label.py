import configparser

from movierender.config import _parse_text_props


def test_channel_label_font_size_parsed():
    cfg = configparser.ConfigParser()
    cfg.read_dict({"PANEL-1": {"channel_label.font_size": "30", "channel_label.font_name": "Helvetica"}})
    props = _parse_text_props(cfg["PANEL-1"], "channel_label")
    assert props.font_size == 30
    assert props.font_name == "Helvetica"
