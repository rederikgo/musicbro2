"""REST API wrappers

Wrappers for Telegram, Last.fm
"""
from datetime import datetime, timezone
import sys
import time
from typing import Optional

from requests import Request, Session

from app.config import Config


# Wrapper parent class
class Requester:
    def __init__(self, token=None, proxies=None, rate_limit=None, error_retries=None, cfg=Config()):
        if not token:
            token = cfg.lastfm.token
        if not proxies:
            proxies = {}
        if not rate_limit:
            rate_limit = cfg.lastfm.rate_limit
        if not error_retries:
            error_retries = cfg.lastfm.error_retries

        # Setup logging
        self.cfg = cfg
        self.logger = cfg.get_logger()

        self.token = token
        self.headers = {'User-Agent': 'MusicBro2/alpha'}
        self.proxies = proxies

        self.error_retries = error_retries
        self.rate_limit = rate_limit

        self.request_time = 0

    # Get url via requests. Return response with status 200 or raise an error
    def _get_url(self, url, params=None):
        if not params:
            params = {}
        for _ in range(self.error_retries):
            self._request_throttle()
            self.request_time = time.time()
            try:
                s = Session()
                prepped = Request('GET', url, params=params, headers=self.headers).prepare()
                response = s.send(prepped, proxies=self.proxies)
                self.last_response = response
                if response.status_code == 200 and type(response.json()) == dict:
                    log_message = {'url': url, 'status_code': response.status_code} | params
                    self.logger.debug(f'Requester:Request:{log_message}')
                    return response.json()
                else:
                    log_message = {'url': url, 'status_code': response.status_code} | params
                    self.logger.warning(f'Requester:Request:{log_message}')
            except:
                self.logger.error(f'{sys.exc_info()} on {url}')

        self.logger.error('Requester:Too many request errors in a row. Terminating session')
        raise UserWarning('Requester:Too many request errors in a row. Terminating session')

    # Rate limiter, no more than n requests per second
    def _request_throttle(self):
        n = self.rate_limit
        since_last_request = time.time() - self.request_time
        if since_last_request < 1/n:
            time.sleep(1/n - since_last_request)


# Last.fm wrapper subclass
class LastFmRequester(Requester):
    api_endpoint = "https://ws.audioscrobbler.com/2.0/?"

    # Class for track data
    class Track:
        def __init__(self, track: dict, source: str = 'web'):
            if source == 'web':
                self.artist_title = track['artist']['#text']
                self.artist_mbid = track['artist']['mbid']
                self.album_title = track['album']['#text']
                self.album_mbid = track['album']['mbid']
                self.track_title = track['name']
                self.track_mbid = track['mbid']
                self.scrobble_date = datetime.fromtimestamp(int(track['date']['uts']), tz=timezone.utc)
            else:
                self.artist_title = track['artist_title']
                self.artist_mbid = track['artist_mbid']
                self.album_title = track['album_title']
                self.album_mbid = track['album_mbid']
                self.track_title = track['track_title']
                self.track_mbid = track['track_mbid']
                self.scrobble_date = track['scrobble_date']

    # Get the list of Track objects, representing scrobbled tracks for user between datetimes
    def get_recent_tracks(self, user_name: str, from_time: datetime, to_time: datetime = datetime.utcnow()) -> Optional[list]:
        params = {
            'method': 'user.getrecenttracks',
            'api_key': self.token,
            'user': user_name,
            'from': str(int(from_time.timestamp())),
            'to': str(int(to_time.timestamp())),
            'limit': self.cfg.lastfm.per_page,
            'format': 'json'
        }

        self.logger.debug(f'Requester:Requesting tracks for user \'{user_name}\' from {from_time} to {to_time}')
        response = self._get_page(params, 1)
        if response:
            tracklist = self._extract_data(response)
        else:
            self.logger.info(f'Requester:Total 0 tracks extracted for user \'{user_name}\'')
            return None

        total_tracks = int(response['recenttracks']['@attr']['total'])
        total_pages = int(response['recenttracks']['@attr']['totalPages'])
        if total_pages > 1:
            for page in range(2, total_pages + 1):
                if response:
                    response = self._get_page(params, page)
                    tracklist += self._extract_data(response)
                else:
                    break

        if total_tracks != len(tracklist):
            self.logger.info(f'Requester:Total number of tracks does not match parsed output for {params["user_name"]} from {params["from"]} to {params["to"]}.'
                              f' Expected {total_tracks}, got {len(tracklist)}')

        self.logger.info(f'Requester:Total {len(tracklist)} track(s) extracted for user \'{user_name}\'')
        return tracklist

    # Call request with the page specified
    def _get_page(self, params: dict, page_num: int) -> Optional[dict]:
        params['page'] = page_num
        r = self._get_url(LastFmRequester.api_endpoint, params)
        if self._check_response_status(r):
            return r
        else:
            return None

    # Check if there is an error in Last.fm response
    def _check_response_status(self, response: dict) -> bool:
        if 'error' in response.keys():
            self.logger.warning(f'Requester:Got error in Last.fm response:{response}')
            return False
        else:
            return True

    # Parse json for scrobbled tracks, return the list of Track objects
    def _extract_data(self, inputdict: dict) -> list:
        if type(inputdict['recenttracks']['track']) != list:
            return []

        extracted_tracks = []
        for track in inputdict['recenttracks']['track']:
            try:
                if track['@attr']['nowplaying'] == 'true':
                    continue
            except KeyError:
                pass

            extracted_tracks.append(self.Track(track))
        self.logger.debug(f'Requester:Extracted {len(extracted_tracks)} track(s)')
        return extracted_tracks


# Telegram wrapper subclass
class TeleRequester(Requester):
    api_endpoint = 'https://api.telegram.org'

    # Construct url string from parameters
    def _make_url(self, method):
        url = '/'.join([self.api_endpoint, 'bot' + self.token, method])
        return url

    # Check and report response status
    def _check_response_status(self, response):
        if response['ok'] is True:
            return True
        else:
            return False

    # Self-test bot, return status
    def self_test(self):
        url = self._make_url('getMe')
        response = self._get_url(url)
        return self._check_response_status(response)

    # Send specified message to the specified chat, return status
    def send_message(self, chat_id, text):
        method = 'sendMessage'
        params = {
            'chat_id': chat_id,
            'text': text
        }
        url = self._make_url(method)
        response = self._get_url(url, params=params)
        return self._check_response_status(response)

    # Get updates
    def get_updates(self):
        url = self._make_url('getUpdates')
        return self._get_url(url)

    # Clear updates
    def clear_updates(self, offset):
        method = 'getUpdates'
        params = {
            'offset': offset
        }
        url = self._make_url(method)
        response = self._get_url(url, params=params)
        return self._check_response_status(response)
