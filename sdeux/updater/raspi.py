# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
__author__ = 'chiesa'
__copyright__ = "Copyright Alpes Lasers SA"

import logging
import os
import sys
import time
from logging import FileHandler, Formatter, StreamHandler

from sdeux.updater.writer import terminalLogger, FirmwareUpdater


def main():
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.INFO)
    lfh = FileHandler(filename=os.path.expanduser('~/s2updater.log'))
    lfh.setFormatter(Formatter(fmt='{asctime}:{levelname}: {message}', style='{'))
    lfh.setLevel(logging.INFO)
    rootLogger.addHandler(lfh)
    lsh = StreamHandler(stream=sys.stdout)
    terminalLogger.addHandler(lsh)

    fwu = FirmwareUpdater(port='/dev/ttyUSB0',
                          firmware_path='/home/pi/updater/s2_2005_signed.bin',
                          stm32flash_path='/usr/bin/stm32flash',
                          new_firmware_version=3832)

    terminalLogger.info('Please connect S2 for update')

    # check if only one S2 is connected
    # if False:
    #     sys.exit(1)

    while True:
        if fwu.is_connected():
            break
        time.sleep(1.0)

    fwu.upgrade()



if __name__ == '__main__':
    main()
