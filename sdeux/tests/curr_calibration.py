# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
import argparse
import logging

from dms import DMSManager
from sdeux.auto_detect import init_driver
from sdeux.calibr.commands import S2CurrentCalibrationCommand
from sdeux.s2Qualification.ssrv_communication import check_sample_in_db

from sdeux.utils.s2admin import get_s2, get_calibration


logger = logging.getLogger(__name__)

__author__ = 'chiesa'
__copyright__ = "Copyright Alpes Lasers SA"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--setup", default='HP/S2/SETUPS/CALIBRATION')
    args = parser.parse_args()
    dms = DMSManager()
    setup = dms.get_setup(args.setup)
    s2_th = setup.get_instrument('S2')
    vm_th = setup.get_instrument('VM')
    with dms.acquire_instruments(s2_th, vm_th):
        s2 = init_driver(s2_th)
        s2.set_up()
        al_identifier = s2.get_al_identifier()
        print('name: {}'.format(al_identifier))
        print('software version: {}'.format(s2.sw_version))
        print('hw version: {}'.format(s2.hw_version))
        check_sample_in_db(al_identifier, s2.hw_version)
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

        c = S2CurrentCalibrationCommand(device_al_id=al_identifier,
                                        s2_device=s2,
                                        voltmeter=vm_th,
                                        station_name='/'.join(args.setup.split('/')[:1]),
                                        setup_name=args.setup)
        c.execute()


if __name__ == '__main__':
    main()






