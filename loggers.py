import os
import json
import logging
import logging.config

ROOT_DIR = os.path.abspath(os.curdir)

def create_log_dir(dir: str) -> None:
    if not os.path.exists(dir):
        os.mkdir(dir)

def init_logger(file_path: str, name: str) -> logging:
    create_log_dir(f"{ROOT_DIR}/log/")
    with open(f"{ROOT_DIR}/{file_path}", "r") as f:
        dict_config = json.load(f)
        dict_config["loggers"][name] = dict_config["loggers"][name]
    logging.config.dictConfig(dict_config)
    return logging.getLogger(name)
