from dataclasses import dataclass
from functools import wraps
import logging
import typing
import logging.config

import yaml


def _check_types(hints, params):
    for key in params.keys():
        if not isinstance(params[key], hints[key]):
            raise TypeError(f'Expected type {hints[key]} for argument {key}, got {type(params[key])} instead')


def force_types(cl):
    def decorate(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            hints = typing.get_type_hints(func)
            _check_types(hints, kwargs)
            return func(*args, **kwargs)
        return wrapper

    cl.__init__ = decorate(cl.__init__)
    return cl


class Config:
    def __init__(self, path='..\\config\\config.yaml'):
        try:
            with open(path, 'r', encoding="utf-8") as configfile:
                cfg = yaml.safe_load(configfile)
        except IOError:
            raise SystemExit('Config: Can\'t open config file. Closing...')

        cfg = self.remove_spaces_from_keys(cfg)

        self.database = self.Database(**cfg['database'])
        self.logger = self.Logger(**cfg['logger'])
        self.lastfm = self.Lastfm(**cfg['lastfm'])

    @force_types
    @dataclass
    class Database:
        host: str
        port: int
        user: str
        password: str
        database: str

    @force_types
    @dataclass
    class Logger:
        name: str
        config: str

    @force_types
    @dataclass
    class Lastfm:
        token: str
        per_page: int

    def remove_spaces_from_keys(self, d: dict) -> dict:
        keys = [*d]
        for key in keys:
            new_key = key.replace(' ', '_')
            d[new_key] = d.pop(key)
            if type(d[new_key]) is dict:
                d[new_key] = self.remove_spaces_from_keys(d[new_key])
        return d

    def get_logger(self) -> logging.Logger:
        try:
            with open(self.logger.config, 'r') as logging_cfg_file:
                logging_cfg = yaml.safe_load(logging_cfg_file)
        except IOError:
            raise SystemExit('Config: Can\'t load logging config. Closing...')

        logging.config.dictConfig(logging_cfg)

        return logging.getLogger(self.logger.name)
