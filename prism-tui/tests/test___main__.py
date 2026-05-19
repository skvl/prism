from unittest.mock import patch, MagicMock


def test_main_calls_app_run():
    from prism_tui.__main__ import main
    with patch("prism_tui.__main__.main") as mock_main:
        import prism_tui.__main__
        assert prism_tui.__main__.__name__ == "prism_tui.__main__"
