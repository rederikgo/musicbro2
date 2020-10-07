import datetime
from typing import Optional, Tuple

import psycopg2

from app.config import Config


class DB:
    def __init__(self, cfg: Config) -> None:
        self.logger = cfg.get_logger()
        database = cfg.database.database
        user = cfg.database.user
        password = cfg.database.password
        host = cfg.database.host
        port = cfg.database.port

        self.conn = psycopg2.connect(host=host, port=port, dbname=database, user=user, password=password)
        self.cur = self.conn.cursor()
    
    def get_utc_now(self) -> datetime:
        return datetime.datetime.utcnow()
    
    def close(self) -> None:
        self.cur.close()
        self.conn.close()


class LastfmUpdater(DB):
    # LAST.FM UPDATER PROCEDURES
    # Get artist id by mbid or by name
    def get_artist_id(self, name: str, mbid: str = '') -> Optional[int]:
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
            self.logger.debug(f'Database: Cant find artist <{name}> id in the database')
            result = None
        if result and self.cur.rowcount > 1:
            self.logger.error(f'Database: Multiple results for <{name}> id search. Skipping...')
            result = None
        if result:
            result = result[0][0]
        return result

    # Get artist name
    def get_artist_name(self, artist_id: int) -> Optional[str]:
        self.cur.execute("""
            SELECT artists.name 
            FROM artists 
            WHERE artists.id = %s
        """, (artist_id,))
        result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find artist id <{artist_id}> id in the database')
            result = None
        if result:
            result = result[0][0]
        return result

    # Get artist id from album id
    def get_artist_id_from_album(self, album_id: int) -> Optional[int]:
        self.cur.execute("""
            select albums.artist
            from albums
            where albums.id = %s
        """, (album_id, ))
        result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find artist id by album <{album_id}> id in the database')
            result = None
        if result:
            result = result[0][0]
        return result

    # Add artist
    def add_artist(self, name: str, mbid: str = '') -> int:
        self.cur.execute("""
            INSERT INTO artists (mbid, name, ts)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (mbid, name, self.get_utc_now()))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        self.logger.debug(f'Database: Artist <{name}> added with id <{result}>')
        return result

    # Get album id
    def get_album_id(self, title: str, artist_id: int, mbid: str = '') -> Optional[int]:
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
            self.logger.debug(f'Database: Cant find album <{title}> for artist <{artist_name}> by id in the database')
            result = None
        if result and self.cur.rowcount > 1:
            artist_name = self.get_artist_name(artist_id)
            self.logger.error(f'Database: Multiple results for album <{title}> of artist <{artist_name}> during id search. Skipping...')
            result = None
        if result:
            result = result[0][0]
        return result

    # Get album title
    def get_album_title(self, album_id: int) -> str:
        self.cur.execute("""
            select albums.title
            from albums
            where albums.id = %s
        """, (album_id, ))
        result = self.cur.fetchall()

        if not result:
            self.logger.debug(f'Database: Cant find album title by id <{album_id}> in the database')
            result = None
        if result:
            result = result[0][0]
        return result

    # Add album
    def add_album(self, title: str, artist_id: int, mbid: str = '') -> int:
        self.cur.execute("""
            insert into albums (mbid, title, artist, release_date, ts)
            values (%s, %s, %s, null, %s)
            returning id
        """, (mbid, title, artist_id, self.get_utc_now()))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        artist_name = self.get_artist_name(artist_id)
        self.logger.debug(f'Database: Album <{title}< for artist <{artist_name}> added with id <{result}>')
        return result

    # Get track id
    def get_track_id(self, title: str, album_id: int, mbid: str = '') -> Optional[int]:
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
            self.logger.debug(f'Database: Cant find track <{title}> from album <{album_title}> of artist <{artist_name}> in the database')
            result = None
        if result and self.cur.rowcount > 1:
            album_title = self.get_album_title(album_id)
            artist_name = self.get_artist_name(self.get_artist_id_from_album(album_id))
            self.logger.error(f'Database: Multiple results for track <{title}< from <{album_title}> of <{artist_name}> during id search. Skipping...')
            result = None
        if result:
            result = result[0][0]
        return result

    # Add track
    def add_track(self, title: str, album_id: int, mbid: str = '') -> int:
        self.cur.execute("""
            insert into tracks (mbid, title, album, ts)
            values (%s, %s, %s, %s)
            returning id
        """, (mbid, title, album_id, self.get_utc_now()))
        result = self.cur.fetchall()[0][0]
        self.conn.commit()
        return result

    # Add scrobbled track to recent tracks
    def add_scrobbled_track(self, user: int, artist_name: str, artist_mbid: str, album_title: str, album_mbid: str, track_title: str, track_mbid: str, scrobbled: datetime) -> Optional[Tuple]:
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
        scrobbled_id = self.cur.fetchall()[0][0]  # type: int

        return artist_id, album_id, track_id, scrobbled_id

    # Add user
    def add_user(self, lastfm_name: str, telegram_name: str) -> int:
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
