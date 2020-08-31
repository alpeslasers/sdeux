# -*- coding: utf-8 -*-

import logging
import os
import subprocess
import sys
import time
from logging import FileHandler, Formatter, StreamHandler

from sdeux.auto_detect import init_driver
from sdeux.serial_handler import S2SerialHandler

logger = logging.getLogger(__name__)
terminalLogger = logging.getLogger('{}.{}'.format(__name__, 'terminal'))

__author__ = 'chiesa'
__copyright__ = "Copyright 2018, Alpes Lasers SA"


class FirmwareUpdater:

    FINISHED_STEP = 'finished'

    def __init__(self,
                 port,
                 firmware_path,
                 stm32flash_path,
                 new_firmware_version):
        """
        :param port: the RS232 port path,
        :param firmware_path: the path to the firmware binary,
        :param stm32flash_path: the path to the stm32flash installation program,
        :param int new_firmware_version: the version number of the firmware binary to be installed,
        """

        self.port = port
        self.firmwarePath = firmware_path
        self.stm32flashPath = stm32flash_path
        self.newFirwareVersion = int(new_firmware_version)
        self.s2DeviceId = None
        self.th = None
        self.s2 = None
        self.s2Info = None
        self.s2Settings = None
        self.s2Calibration = None
        self.s2InfoAfter = None
        self.s2SettingsAfter = None
        self.s2CalibrationAfter = None
        self.totalSteps = 6
        if not os.path.exists(self.stm32flashPath):
            raise Exception
        if not os.path.exists(self.firmwarePath):
            raise Exception
        if not os.access(self.firmwarePath, os.R_OK):
            raise Exception
        if not os.access(self.stm32flashPath, os.X_OK):
            raise Exception

    def connect(self):
        self.th = S2SerialHandler(self.port)
        self.th.open()
        self.s2 = init_driver(self.th)
        self.s2.set_up()

    def disconnect(self):
        if self.th:
            self.th.close()
            self.th = None
            self.s2 = None

    def is_connected(self):
        try:
            self.connect()
            return True
        except Exception as e:
            logger.debug(e, exc_info=1)
            return False
        finally:
            self.disconnect()

    def log_step(self, step, message):
        terminalLogger.info('[{}/{}, S2 #{}] {}'.format(step if step != self.FINISHED_STEP else self.totalSteps,
                                                        self.totalSteps,
                                                        self.s2DeviceId,
                                                        message))

    def execute(self):
        try:
            self.connect()
            if self.s2.info.sw_version == self.newFirwareVersion:
                self.log_step(self.FINISHED_STEP,
                              'S2 already at firmware version {}: doing nothing.'.format(self.newFirwareVersion))
                return
            self.s2Info = self.s2.info
            self.s2Settings = self.s2.settings
            self.s2Calibration = self.s2.calibration
            self.s2DeviceId = self.s2.device_id
            terminalLogger.info('Connected to S2 #{}.'
                                '\n >> DO NOT DISCONNECT THE DEVICE! '
                                '\n >> DO NOT SWITCH ANYTHING OFF'.format(self.s2DeviceId))
            logger.info('before={}'.format(dict(info=self.s2Info.to_dict(),
                                                settings=self.s2Settings.to_dict(),
                                                calibration=self.s2Calibration.to_dict())))
            self.log_step(0, 'Rebooting to bootloader mode.')
            self.s2.reboot_to_bootloader()
            time.sleep(2)
            self.disconnect()
            self.log_step(1, 'Writing firmware.')
            self.write_firmware()
            self.log_step(2, 'Rebooting to operational mode.')
            self.boot_to_firmware()
            self.log_step(3, 'Checking communication.')
            self.connect()
            self.log_step(4, 'Rewriting configuration.')
            self.s2.apply_calibration(self.s2Calibration, store=True)
            self.s2.reload_calibration()
            self.s2.set_configuration(device_id=self.s2Info.device_id,
                                      laser_id=self.s2Info.laser_id)
            self.s2.reload_info()
            self.s2InfoAfter = self.s2.info
            self.s2SettingsAfter = self.s2.settings
            self.s2CalibrationAfter = self.s2.calibration
            logger.info('after={}'.format(dict(info=self.s2InfoAfter.to_dict(),
                                               settings=self.s2SettingsAfter.to_dict(),
                                               calibration=self.s2CalibrationAfter.to_dict())))
            self.disconnect()
            if self.is_correctly_updated():
                self.log_step(self.FINISHED_STEP, 'Firmware update finalized.')
            else:
                self.log_error_occurred()
        except Exception as e:
            logger.exception(e)
            self.log_error_occurred()
        finally:
            self.disconnect()
            terminalLogger.info('Update procedure finished: you may now disconnect the S2.')

    def log_error_occurred(self):
        terminalLogger.error('Some errors occurred. Please submit log file to AlpesLasers')

    def is_correctly_updated(self):
        return True

    def boot_to_firmware(self):
        retry_count = 3
        while retry_count > 0:
            try:
                subprocess.check_call([self.stm32flashPath, '-b', '38400', '-g', '0', self.port])
                break
            except Exception as e:
                logger.info(e, exc_info=1)
                retry_count -= 1
                if retry_count == 0:
                    raise
                else:
                    time.sleep(1)
        time.sleep(1)

    def write_firmware(self):
        retry_count = 2
        while retry_count > 0:
            try:
                subprocess.check_call([self.stm32flashPath, '-b', '38400', '-w',
                                       self.firmwarePath, self.port])
                break
            except Exception as e:
                logger.info(e, exc_info=1)
                retry_count -= 1
                if retry_count == 0:
                    raise
                else:
                    time.sleep(1)
        time.sleep(1)

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

    fwu.execute()


if __name__ == '__main__':
    main()
