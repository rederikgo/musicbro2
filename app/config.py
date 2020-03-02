import logging
import logging.handlers
import logging.config
import os

import yaml


def load_cfg(path):
    try:
        with open(path, 'r') as cfgfile:
            return yaml.safe_load(cfgfile)
    except:
        print('Main: Cant open config file. Closing...')
        raise SystemExit

def get_logger(cfg):
    try:
        with open(cfg['logger']['config'], 'r') as logging_cfg_file:
            logging_cfg = yaml.safe_load(logging_cfg_file)
    except:
        print('Main: Cant load logging config. Closing...')
        raise SystemExit
    logging.config.dictConfig(logging_cfg)
    return logging.getLogger(cfg['logger']['name'])