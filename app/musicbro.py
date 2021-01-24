from app.config import Config
from app.import_lastfm import LastFmPipe


def main():    
    # Load config and get logger
    cfg = Config()
    logger = cfg.get_logger()

    # Let's go
    logger.info('Main:Session started')
    lastfm = LastFmPipe(cfg)
    lastfm.update_all()
    logger.info('Main:Session closed')

if __name__ == '__main__':
    main()
