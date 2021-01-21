from app.config import Config


def main():    
    # Load config and get logger
    cfg = Config('..\\config\\config.yaml')
    logger = cfg.get_logger()

    # Let's go
    logger.info('Main: Session started')


if __name__ == '__main__':
    main()
