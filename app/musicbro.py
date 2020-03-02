import os

import yaml

import app.config as config
from app.database import DBScheduler


def main():    
    # Load config and get logger
    cfg = config.load_cfg('..\\config\\config.yaml')
    logger = config.get_logger(cfg)

    # Let's go
    logger.info('Main: Session started')


if __name__ == '__main__':
    main()