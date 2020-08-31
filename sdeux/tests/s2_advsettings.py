# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
import argparse
import logging
from time import sleep

from dms import DMSManager
from sdeux.auto_detect import init_driver

from sdeux.utils.s2admin import get_s2, get_calibration

logger = logging.getLogger(__name__)

__author__ = 'chiesa'
__copyright__ = "Copyright Alpes Lasers SA"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", default='EXPERIMENTAL/TEST/SETUPS/CALIBRATION')
    args = parser.parse_args()
    dms = DMSManager()
    setup = dms.get_setup(args.setup)
    s2_th = setup.get_instrument('S2')
    with dms.acquire_instruments(s2_th):
        s2 = init_driver(s2_th)
        s2.set_up()
        print('name: {}'.format(s2.get_al_identifier()))
        print('software version: {}'.format(s2.sw_version))
        board = get_s2(s2.device_id)
        if not board:
            raise Exception('board with serial_number {} not found in database!'.format(s2.device_id))
        if not s2.hw_version == board['hardware_revision']:
            raise Exception('database mismatch: board hw = {}, '
                            'database hw = {}'.format(s2.hw_version,
                                                      board['hardware_revision']))
        if not str(s2.sw_version) == str(board['firmware_version']):
            raise Exception('database mismatch, board sw = {}, '
                            'database sw = {}'.format(s2.sw_version,
                                                      board['firmware_version']))
        calibration = get_calibration(s2.device_id)
        print(s2.calibration.to_dict())
        print(calibration)

        logger.info('DAC - ADC - voltage')

        s2.set_settings(pulse_period=1000, pulse_width=1000,
                        pulsing_mode='internal', voltage=1.0,
                        current_limit=10.0)
        s2.set_advanced_settings(output_voltage_set_raw=1,
                                 DCDC_mode=1)
        out = []
        for i in range(650, 4095, 50):
            s2.set_advanced_settings(output_voltage_set_raw=i,
                                     DCDC_mode=1)
            sleep(1)

            s2.reload_info()
            s2.reload_settings()
            s2.reload_advanced_settings()

            print(i, s2.output_voltage_measured_raw)


if __name__ == '__main__':
    main()






