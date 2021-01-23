import os

import pytest
import yaml

from app.config import Config
from app.database import LastfmUpdater
from app.rest_wrappers import LastFmRequester

@pytest.fixture(scope="module")
def db():
    cfg = Config('test_data\\config.yaml')
    db_setup = LastfmUpdater(cfg)
    db_setup.conn.autocommit = True
    db_setup.cur.execute("""
        CREATE DATABASE musicbro2_test TEMPLATE musicbro2_template;
    """)

    cfg.database.database = 'musicbro2_test'
    db = LastfmUpdater(cfg)

    yield db
    db.close()
    db_setup.cur.execute("""
            DROP DATABASE musicbro2_test;
        """)
    db_setup.close()


@pytest.fixture(scope="module")
def cases():
    with open(os.getcwd() + '\\test_data\\test_cases.yaml', 'r') as cases_file:
        return yaml.safe_load(cases_file)


def test_connection(db):
    assert db.conn.closed == 0
    db.cur.execute("SELECT 1")


def test_add_user(db, cases):
    test_cases = cases['database']['add_user']
    for case in test_cases:
        assert db.add_user(test_cases[case]['input']['lastfm_username'], test_cases[case]['input']['telegram_handle']) == test_cases[case]['output']


def test_add_recent_track(db, cases):
    test_cases = cases['database']['scrobble_track']
    for case in test_cases:
        c = test_cases[case]
        track = LastFmRequester.Track(c['input'], source='test_case')
        assert db.add_scrobbled_track(c['input']['user'], track) == tuple(c['output'])
    pass
