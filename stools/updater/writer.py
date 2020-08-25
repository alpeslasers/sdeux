# -*- coding: utf-8 -*-

import logging
import subprocess
import time

from stools.auto_detect import init_driver
from stools.serial_handler import S2SerialHandler

logger = logging.getLogger(__name__)
terminalLogger = logging.getLogger('{}.{}'.format(__name__, 'terminal'))

__author__ = 'gregory'
__copyright__ = "Copyright 2018, Alpes Lasers SA"


class FirmwareUpdater:

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
        terminalLogger.info('[{}/{}, #{}] {}'.format(step if step != 'finished' else self.totalSteps,
                                                     self.totalSteps,
                                                     self.s2DeviceId,
                                                     message))

    def execute(self):
        try:
            self.connect()
            self.s2Info = self.s2.info
            self.s2Settings = self.s2.settings
            self.s2Calibration = self.s2.calibration
            self.s2DeviceId = self.s2.device_id
            terminalLogger.info('Connected to S2 #{}.'
                                '\n >> DO NOT DISCONNECT THE DEVICE! '
                                '\n >> DO NOT SWITCH ANYTHING OFF'.format(self.s2DeviceId))
            logger.info('S2Info; S2Settings; S2Calibration')
            logger.info('{}; {}; {}'.format(self.s2Info.to_dict(),
                                            self.s2Settings.to_dict(),
                                            self.s2Calibration.to_dict()))
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
            self.log_step(4, 'Rewrite calibration, laser_id and device_id.')
            self.s2.apply_calibration(self.s2Calibration, store=True)
            self.s2.reload_calibration()
            self.s2.set_configuration(device_id=self.s2Info.device_id,
                                      laser_id=self.s2Info.laser_id)
            self.s2.reload_info()
            self.s2InfoAfter = self.s2.info
            self.s2SettingsAfter = self.s2.settings
            self.s2CalibrationAfter = self.s2.calibration
            logger.info('S2InfoAfter; S2SettingsAfter; S2CalibrationAfter')
            logger.info('{}; {}; {}'.format(self.s2InfoAfter.to_dict(),
                                            self.s2SettingsAfter.to_dict(),
                                            self.s2CalibrationAfter.to_dict()))
            self.disconnect()
            if self.is_correctly_updated():
                self.log_step('finished', 'firmware update finalized.')
            else:
                self.log_step('finished', 'some errors occurred. Please submit log file to AlpesLasers.')
        finally:
            self.disconnect()

    def is_correctly_updated(self):
        return True

    def boot_to_firmware(self):
        retry_count = 3
        while retry_count > 0:
            try:
                subprocess.check_call([self.stm32flashPath, '-b', '38400', '-g', '0', self.port])
                break
            except Exception as e:
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
            except Exception:
                retry_count -= 1
                if retry_count == 0:
                    raise
                else:
                    time.sleep(1)
        time.sleep(1)



def update_multiple(fw_file, ports):
    try:
        with open(fw_file):
            pass
    except Exception as e:
        logger.critical('Cannot open firmware file at "{}", {}'.format(fw_file, e))
    failures = []
    ports=['/dev/ttyUSB0']
    for port in ports:
        th = S2SerialHandler(port)
        th.open()
        try:
            s2 = init_driver(th)
            s2.set_up()
            logger.info('[{}] Connected to S2 #{}; Loading bootloader...'.format(port, s2.device_id))
            s2.reboot_to_bootloader()
            time.sleep(2)
        except Exception as e:
            logger.error('[{}] Update FAILED!! Could not initialize S-2: {}'.format(port, e), exc_info=1)
            failures.append(port)
            continue
        finally:
            th.close()

        try:
            write_firmware(fw_file, port)
        except Exception as e:
            failures.append(port)
            continue



if __name__ == '__main__':
    import argparse
    logging.basicConfig(level=logging.INFO)

    fw_file='/home/local/olgare/PycharmProjects/s2/gen2005/firmware/cubemx/s2_2005_signed.bin'
    port='/dev/ttyUSB0'

    try:
        update_multiple(fw_file, port)
    except Exception as e:
        logger.error('[{}] Writing firmware failed. "{}"'.format(port, e))
