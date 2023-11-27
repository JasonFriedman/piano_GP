#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pathlib import Path

log_folder = Path("output/temp/logs")
log_folder.mkdir(parents=True, exist_ok=True)


def get_logger_for_this_file(name, debug_in_console=False, info_in_console=False):
    global log_folder
    
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    ch_level = logging.WARNING
    if info_in_console:
        ch_level = logging.INFO
    if debug_in_console:
        ch_level = logging.DEBUG
    
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(ch_level)
    
    logger.addHandler(ch)
    
    log_file = log_folder / f"{name}.log"
    print("log", log_file)
    
    fh = logging.FileHandler(filename=log_file)
    fh.setFormatter(formatter)
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
    
    return logger
    
# if __name__ == "__main__":
#     print(get_log_folder())
