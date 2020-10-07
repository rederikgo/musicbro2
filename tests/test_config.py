import logging
import pytest

# from testfixtures import LogCapture

from app.config import Config


def test_load_cfg():
    path = 'test_data\\config.yaml'
    cfg = Config(path)
    assert cfg.lastfm.token == ''

    with pytest.raises(SystemExit):
        path = 'test_data\\nonexisting.yaml'
        cfg = Config(path)

    with pytest.raises(TypeError):
        path = 'test_data\\config_type_error.yaml'
        cfg = Config(path)
