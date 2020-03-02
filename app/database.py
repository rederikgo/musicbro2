import datetime
import logging

import psycopg2


class DB:
    def __init__(self, cfg):
        self.logger = logging.getLogger(cfg['logger']['name']) # <- logger details
        database = cfg['database']['database']
        user = cfg['database']['user']
        password = cfg['database']['password']
        host = cfg['database']['host']
        port = cfg['database']['port']

        self.conn = psycopg2.connect(host=host, port=port, dbname=database, user=user, password=password)
        self.cur = self.conn.cursor()
    
    def get_utc_now(self):
        return datetime.datetime.utcnow()
    
    def close(self):
        self.cur.close()
        self.conn.close()


class DBScheduler(DB):
    # SESSION PROCEDURES
    # def init_session(self):
    #     self._get_new_session_id()
    #     self._init_new_session()
    #     self.logger.info('Session {} started at {}'.format(self.session_id, self.session_started))
    #     self.logger.debug('Database connection operational')
    #
    # def _get_new_session_id(self):
    #     self.cur.execute('SELECT MAX(session_id) FROM scheduler_sessions')
    #     result = self.cur.fetchall()
    #     if result[0][0] == None:
    #         self.session_id = 1
    #     else:
    #         self.session_id = result[0][0] + 1
    #     self.logger.debug('Session id set to {}'.format(self.session_id))
    #
    # def _init_new_session(self):
    #     self.session_started = self.get_utc_now()
    #     self.cur.execute('INSERT INTO scheduler_sessions VALUES (%s, %s, NULL)', (self.session_id, self.session_started))
    #     self.conn.commit()
    #     self.logger.debug('New session logged to the db')
    #
    # def find_and_add_orphaned_tasks(self):
    #     orphaned_tasks = self._find_orphaned_tasktypes()
    #     if orphaned_tasks == []:
    #         self.logger.debug('No orphaned tasks found')
    #         return
    #     for task in orphaned_tasks:
    #         task_id, task_type = task
    #         self.add_task(task_id, task_type)
    #         self.logger.debug('Orphaned task \'{}\' scheduled to run immediately'.format(task_type))
    #     self.logger.info('{} orphaned tasks scheduled'.format(len(orphaned_tasks)))
    #
    # def _find_orphaned_tasktypes(self):
    #     self.cur.execute("""
    #         SELECT scheduler_task_types.task_id, scheduler_task_types.task_type
    #         FROM scheduler_task_types
    #         WHERE NOT EXISTS (
    #             SELECT scheduler_tasks.task_id
    #             FROM scheduler_tasks
    #             WHERE scheduler_task_types.task_id=scheduler_tasks.task_id AND scheduler_tasks.session_id IS NULL
    #         )
    #     """)
    #     orphaned_tasks = self.cur.fetchall()
    #     return orphaned_tasks
    #
    # def get_pending_tasks(self):
    #     self.cur.execute("""
    #         SELECT scheduler_task_types.task_id, scheduler_task_types.task_type, scheduler_task_types.module_name, scheduler_tasks.scheduled_date
    #         FROM scheduler_task_types
    #         JOIN scheduler_tasks
    #         ON scheduler_tasks.task_id = scheduler_task_types.task_id
    #         WHERE scheduler_tasks.scheduled_date <= %s AND scheduler_tasks.session_id IS NULL
    #     """, (self.get_utc_now(), ))
    #     pending_tasks = self.cur.fetchall()
    #     self.logger.debug('{} pending tasks found'.format(len(pending_tasks)))
    #     return pending_tasks
    #
    # def add_task(self, task_id, task_type, scheduled_time = 'now'):
    #     if scheduled_time == 'now':
    #         scheduled_time = self.get_utc_now()
    #     self.cur.execute("""
    #         INSERT INTO scheduler_tasks (task_id, scheduled_date, session_id, date_added)
    #         VALUES (%s, %s, NULL, %s)
    #     """, (task_id, scheduled_time, self.get_utc_now()))
    #     self.conn.commit()
    #     self.logger.debug('Task type \'{}\' scheduled for {}'.format(task_type, scheduled_time))
    #
    # def close_task(self, task_id, scheduled_time, task_type):
    #     self.cur.execute("""
    #         UPDATE scheduler_tasks
    #         SET session_id = %s
    #         WHERE task_id = %s AND scheduled_date = %s
    #     """, (self.session_id, task_id, scheduled_time))
    #     self.conn.commit()
    #     self.logger.debug('Closed task \'{}\' scheduled for {}'.format(task_type, scheduled_time))
    #
    # def close_session(self):
    #     self.session_closed = self.get_utc_now()
    #     self.cur.execute('UPDATE scheduler_sessions SET finished_date = %s WHERE session_id = %s', (self.session_closed, self.session_id))
    #     self.conn.commit()
    #     self.logger.debug('Session logged as closed at the db')
    #     self.close()
    #     self.logger.debug('Database connection closed')
    #     self.logger.info('Session {} finished at {}'.format(self.session_id, self.session_closed))
    #     self.logger.info('='*10)

    # LAST.FM UPDATER PROCEDURES
    # Get artist id by mbid or by name
    def get_artist_id(self, name, mbid=''):
        result = None
        if mbid:
            self.cur.execute("""
                SELECT artists.id 
                FROM artists 
                WHERE artists.mbid = %s
            """, (mbid, ))
            result = self.cur.fetchall()
        if not result:
            self.cur.execute("""
                SELECT artists.id 
                FROM artists 
                WHERE artists.name = %s
            """, (name, ))
            result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find artist {name} id in the database')
            result = None
        if result and self.cur.rowcount > 1:
            self.logger.error(f'Database: Multiple results for {name} id search. Skipping...')
            result = None
        if result:
            result = result[0][0]
        return result

    # Get artist name
    def get_artist_name(self, artist_id):
        self.cur.execute("""
            SELECT artists.name 
            FROM artists 
            WHERE artists.id = %s
        """, (artist_id,))
        result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find artist id {artist_id} id in the database')
            result = None
        if result:
            result = result[0][0]
        return result

    # Get artist id from album id
    def get_artist_id_from_album(self, album_id):
        self.cur.execute("""
            select albums.artist
            from albums
            where albums.id = %s
        """, (album_id, ))
        result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find artist id by album {album_id} id in the database')
            result = None
        if result:
            result = result[0][0]
        return result

    # Add artist
    def add_artist(self, name, mbid=''):
        self.cur.execute("""
            INSERT INTO artists (mbid, name, ts)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (mbid, name, self.get_utc_now()))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        self.logger.debug(f'Database: Artist {name} added with id {result}')
        return result

    # Get album id
    def get_album_id(self, title, artist_id, mbid=''):
        result = None
        if mbid:
            self.cur.execute("""
                select albums.id
                from albums
                where albums.mbid = %s
            """, (mbid, ))
            result = self.cur.fetchall()
        if not result:
            self.cur.execute("""
                select albums.id
                from albums
                where albums.title = %s and albums.artist = %s
            """, (title, artist_id))
        result = self.cur.fetchall()

        if not result:
            artist_name = self.get_artist_name(artist_id)
            self.logger.debug(f'Database: Cant find album {title} for artist {artist_name} by id in the database')
            result = None
        if result and self.cur.rowcount > 1:
            artist_name = self.get_artist_name(artist_id)
            self.logger.error(f'Database: Multiple results for album {title} of artist {artist_name} during id search. Skipping...')
            result = None
        if result:
            result = result[0][0]
        return result

    # Get album title
    def get_album_title(self, album_id):
        self.cur.execute("""
            select albums.title
            from albums
            where albums.id = %s
        """, (album_id, ))
        result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find album title by id {album_id} in the database')
            result = None
        if result:
            result = result[0][0]
        return result

    # Add album
    def add_album(self, title, artist_id, mbid=''):
        self.cur.execute("""
            insert into albums (mbid, title, artist, release_date, ts)
            values (%s, %s, %s, null, %s)
            returning id
        """, (mbid, title, artist_id, self.get_utc_now()))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        artist_name = self.get_artist_name(artist_id)
        self.logger.debug(f'Database: Album {title} for artist {artist_name} added with id {result}')
        return result

    # Get track id
    def get_track_id(self, title, album_id, mbid=''):
        result = None
        if mbid:
            self.cur.execute("""
                select tracks.id
                from tracks
                where tracks.mbid = %s
            """, (mbid, ))
            result = self.cur.fetchall()
        if not result:
            self.cur.execute("""
                select tracks.id
                from tracks
                where tracks.title = %s and tracks.album = %s
            """, (title, album_id))
            result = self.cur.fetchall()

        if not result:
            album_title = self.get_album_title(album_id)
            artist_name = self.get_artist_name(self.get_artist_id_from_album(album_id))
            self.logger.debug(f'Cant find track {title} from album {album_title} of artist {artist_name} in the database')
            result = None
        if result and self.cur.rowcount > 1:
            album_title = self.get_album_title(album_id)
            artist_name = self.get_artist_name(self.get_artist_id_from_album(album_id))
            self.logger.error(f'Database: Multiple results for track {title} from {album_title} of {artist_name} during id search. Skipping...')
            result = None
        if result:
            result = result[0][0]
        return result

    # Add track
    def add_track(self, title, album_id, mbid=''):
        self.cur.execute("""
            insert into tracks (mbid, title, album, ts)
            values (%s, %s, %s, %s)
            returning id
        """, (mbid, title, album_id, self.get_utc_now()))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        return result

    # Add scrobbled track to recent tracks
    def add_scrobbled_track(self, user, artist_name, artist_mbid, album_title, album_mbid, track_title, track_mbid, scrobbled):
        if not artist_name or not track_title:
            self.logger.error('Last.fm import: Missing track or artist. Skipping...')
            return
        if not user:
            self.logger.error('Last.fm import: Missing user. Skipping...')
            return
        if not scrobbled:
            self.logger.error('Last.fm import: Missing scrobble time. Skipping...')
            return
        if not album_title:
            album_title = 'NULL'

        artist_id = self.get_artist_id(artist_name, artist_mbid)
        if not artist_id:
            artist_id = self.add_artist(artist_name, artist_mbid)

        album_id = self.get_album_id(album_title, artist_id, album_mbid)
        if not album_id:
            album_id = self.add_album(album_title, artist_id, album_mbid)

        track_id = self.get_track_id(track_title, album_id, track_mbid)
        if not track_id:
            track_id = self.add_track(track_title, album_id, track_mbid)

        self.cur.execute("""
            insert into lastfm (user_id, track, scrobbled, ts)
            values (%s, %s, %s, %s)
            returning id
        """, (user, track_id, scrobbled, self.get_utc_now()))
        scrobbled_id = self.cur.fetchall()[0][0]

        return artist_id, album_id, track_id, scrobbled_id

    # Add user
    def add_user(self, lastfm_name, telegram_name):
        if not lastfm_name:
            self.logger.error('Database: Cant add user without lastfm profile name')
        if not telegram_name:
            self.logger.error('Database: Cant add user without telegram name')

        self.cur.execute("""
            insert into users (lastfm_username, telegram_handle)
            values (%s, %s)
            returning id
        """, (lastfm_name, telegram_name))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        return result
