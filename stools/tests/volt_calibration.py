# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
import argparse
import logging

import numpy
from dms import DMSManager
from pirata.drivers.S2.auto_detect import init_driver
from stools.calibr.analyze import fit_volt_calibration
from stools.calibr.commands import S2VoltageCalibrationCommand
from stools.s2Qualification.ssrv_communication import ssrv_checkin_sample

from stools.utils.s2admin import get_s2, get_calibration

from matplotlib import pyplot as plt

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
        ssrv_checkin_sample(al_identifier, s2.hw_version)
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

        c = S2VoltageCalibrationCommand(device_al_id=al_identifier,
                                        s2_device=s2,
                                        voltmeter=vm_th,
                                        station_name='/'.join(args.setup.split('/')[:1]),
                                        setup_name=args.setup)
        c.execute()
        print(c.calibration)
        fig1 = plt.figure()
        ax1 = fig1.add_subplot(111)
        ax1.plot(c.outputVoltageMeasuredRaw, c.measuredVoltage)
        ax1.plot(c.outputVoltageMeasuredRaw,
                 numpy.polyval([c.calibration['Vout_meas_a'],
                                c.calibration['Vout_meas_b']],
                               c.outputVoltageMeasuredRaw))
        fig2 = plt.figure()
        ax2 = fig2.add_subplot(111)
        ax2.plot(c.measuredVoltage, c.outputVoltageSetRaw)
        ax2.plot(c.measuredVoltage,
                 numpy.polyval([c.calibration['Vout_set_a'],
                                c.calibration['Vout_set_b']],
                               c.measuredVoltage))
        plt.show()


if __name__ == '__main__':
    main()






