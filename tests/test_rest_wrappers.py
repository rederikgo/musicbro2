from datetime import datetime, timezone
import json
import os
import pytest
from unittest import mock

import yaml

from app.rest_wrappers import LastFmRequester
from app.config import Config


@pytest.fixture(scope="module")
def cfg():
    return Config('test_data\\config.yaml')


@pytest.fixture(scope="module")
def cases():
    with open(os.getcwd() + '\\test_data\\test_cases.yaml', 'r') as cases_file:
        return yaml.safe_load(cases_file)


def mocked_requests_get(*args, **kwargs):
    def get_dict_path(nested_dict, value, prepath=()):
        for k, v in nested_dict.items():
            path = prepath + (k,)
            if value == v:
                return path
            elif hasattr(v, 'items'):
                p = get_dict_path(v, value, path)
                if p is not None:
                    return p
            elif type(v) == list:
                if any(value == s for s in v):
                    return path + (v.index(value),)

    class MockResponse:
        with open(os.getcwd() + '\\test_data\\test_cases.yaml', 'r') as cases_file:
            test_cases = yaml.safe_load(cases_file)['lastfm']

        def __init__(self, status_code, json_data):
            self.status_code = status_code
            self.json_data = json_data

        def json(self):
            return self.json_data

    url = args[0].url
    test_cases = MockResponse.test_cases
    if get_dict_path(test_cases, url):
        case_map = get_dict_path(MockResponse.test_cases, url)
        case = case_map[0]
        response_index = case_map[-1]
        return MockResponse(200, json.loads(test_cases[case]['response'][response_index]))
    else:
        return MockResponse(404, None)


@mock.patch('requests.Session.send', side_effect=mocked_requests_get)
def test_bad_reponse(mock_get, cases, cfg):
    test_data = cases['lastfm']['error']
    a = LastFmRequester('wrongkey', rate_limit=10, cfg=cfg)
    with pytest.raises(UserWarning):
        t = a.get_recent_tracks(test_data['input']['user'], to_datetime(test_data['input']['from']),
                                to_datetime(test_data['input']['to']))


@mock.patch('requests.Session.send', side_effect=mocked_requests_get)
def test_error(mock_get, cases, cfg):
    _one_url(mock_get, cases, cfg, 'error')


@mock.patch('requests.Session.send', side_effect=mocked_requests_get)
def test_no_tracks(mock_get, cases, cfg):
    _one_url(mock_get, cases, cfg, 'no_tracks')


@mock.patch('requests.Session.send', side_effect=mocked_requests_get)
def test_no_tracks_nowplaying(mock_get, cases, cfg):
    _one_url(mock_get, cases, cfg, 'no_tracks_nowplaying')


@mock.patch('requests.Session.send', side_effect=mocked_requests_get)
def test_some_tracks_one_page(mock_get, cases, cfg):
    _one_url(mock_get, cases, cfg, 'some_tracks_one_page')


@mock.patch('requests.Session.send', side_effect=mocked_requests_get)
def test_some_tracks_three_pages(mock_get, cases, cfg):
    _one_url(mock_get, cases, cfg, 'some_tracks_three_pages', rate_limit=10)


def _one_url(mock_get, cases, cfg, test_case, rate_limit=None, error_retries=None):
    if not rate_limit:
        rate_limit = cfg.lastfm.rate_limit
    if not error_retries:
        error_retries = cfg.lastfm.error_retries

    test_data = cases['lastfm'][test_case]
    a = LastFmRequester(test_data['input']['key'], rate_limit=rate_limit, error_retries=error_retries, cfg=cfg)
    t = a.get_recent_tracks(test_data['input']['user'], to_datetime(test_data['input']['from']),
                                to_datetime(test_data['input']['to']))

    assert _analyze_output(t) == test_data['output']
    assert [x.args[0].url for x in mock_get.call_args_list] == [url for url in test_data['url']]
    pass


def _analyze_output(output_data):
    if type(output_data) != list:
        return output_data

    tracks = []
    for block in output_data:
        track = {
            'artist_title': block.artist_title,
            'artist_mbid': block.artist_mbid,
            'album_title': block.album_title,
            'album_mbid': block.album_mbid,
            'track_title': block.track_title,
            'track_mbid': block.track_mbid,
            'scrobble_date': block.scrobble_date
        }
        tracks.append(track)
    return tracks


def to_datetime(text: str):
    return datetime.strptime(text, '%d.%m.%Y %H:%M:%S').replace(tzinfo=timezone.utc)
