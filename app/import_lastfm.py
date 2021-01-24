from datetime import datetime, timedelta, timezone

from app.config import Config
from app.database import LastfmUpdater
from app.rest_wrappers import LastFmRequester


class LastFmPipe:
    def __init__(self, cfg: Config):
        self.logger = cfg.get_logger()
        self.db = LastfmUpdater(cfg)
        self.api = LastFmRequester(cfg=cfg)

    def update_all(self):
        self.logger.info('Import_LastFM:Import session started')

        users = self.db.get_users_for_lastfm_import()
        if users:
            self.logger.info(f'Import_LastFM:Found {len(users)} users for input')
        else:
            self.logger.warning('Import_LastFM:No users with enabled lastfm import')
            return

        for user in users:
            user_id = user[0]
            user_name = user[1]

            check_from = self.db.get_last_scrobbled_time(user_id) + timedelta(seconds=1)
            self.logger.info(f"Import_LastFM:Importing tracks for user '{user_name}' from {datetime.strftime(check_from, '%d.%m.%Y %H:%M:%S')}")

            tracks = self.api.get_recent_tracks(user_name, check_from, datetime.fromtimestamp(1136073600, timezone.utc))

            imported = 0
            for track in tracks:
                response = self.db.add_scrobbled_track(user_id, track)
                if response:
                    imported += 1
            self.logger.info(f"Import_LastFM:{imported} tracks imported for user {user_name}")

        self.logger.info('Import_LastFM:Import session closed')
