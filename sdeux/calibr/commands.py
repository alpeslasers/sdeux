# -*- coding: utf-8 -*-
"""
Created by chiesa on 15.08.16

Copyright 2015 Alpes Lasers SA, Neuchatel, Switzerland
"""
import getpass
import logging
from time import sleep

import requests
from configuration_manager import gConfig2

from sdeux.defs import S2_STATUS_OK, S2_PULSING_OFF
from sdeux.calibr.analyze import fit_volt_calibration, fit_curr_calibration

__author__ = 'chiesa'
__copyright__ = "Copyright 2015, Alpes Lasers SA"

logger = logging.getLogger(__name__)


class BaseCommand:

    def __init__(self):
        self.thread = None
        self.errors = None

    def execute(self):
        try:
            self._execute()
        except Exception as e:
            self.errors = e
            self.shut_down()
            raise

    def _execute(self):
        raise NotImplementedError

    def shut_down(self):
        pass


class S2VoltageCalibrationCommand(BaseCommand):

    def __init__(self, device_al_id, voltmeter, s2_device,
                 station_name, setup_name):
        super(S2VoltageCalibrationCommand, self).__init__()
        self.deviceAlId = device_al_id
        self.vm = voltmeter
        self.s2 = s2_device
        self.outputVoltageSetRaw = []
        self.outputVoltageMeasuredRaw = []
        self.measuredVoltage = []
        self.inputVoltage = None
        self.calibration = None
        self.stationName = station_name
        self.setupName = setup_name

    def _execute(self):
        self.s2.set_settings(pulse_period=1000, pulse_width=1000,
                             pulsing_mode='internal', voltage=1.0,
                             current_limit=10.0)
        self.s2.set_advanced_settings(output_voltage_set_raw=1,
                                      DCDC_mode=1)
        for i in range(650, 4095, 50):
            self.s2.set_advanced_settings(output_voltage_set_raw=i,
                                     DCDC_mode=1)
            sleep(1)

            measured_voltage = float(self.vm.query("MEAS:VOLT:DC?"))
            self.s2.reload_info()
            self.s2.reload_settings()
            self.s2.reload_advanced_settings()

            self.outputVoltageSetRaw.append(i)
            self.outputVoltageMeasuredRaw.append(self.s2.output_voltage_measured_raw)
            self.measuredVoltage.append(measured_voltage)

            print("DAC={} ADC={:.2f} V={:.3f}".format(self.outputVoltageSetRaw[-1],
                                                      self.outputVoltageMeasuredRaw[-1],
                                                      self.measuredVoltage[-1]))
            if self.s2.status_label != S2_STATUS_OK:
                raise Exception('S2 status is not OK: {}'.format(self.s2.status_label))

        self.inputVoltage = self.s2.input_voltage_measured

        self.s2.set_advanced_settings(output_voltage_set_raw=1)
        self.shut_down()
        self.calibration = fit_volt_calibration(self.outputVoltageSetRaw,
                                                self.outputVoltageMeasuredRaw,
                                                self.measuredVoltage)
        self.store()

    def shut_down(self):
        self.s2.set_settings(voltage=0, pulsing_mode=S2_PULSING_OFF)
        self.s2.shut_down()

    def store(self):
        ssrv_url = gConfig2.get_url('ssrv_restless')
        data = {'volt_meas_raw': list(self.outputVoltageMeasuredRaw),
                'volt_set_raw': list(self.outputVoltageSetRaw),
                'volt_meas': list(self.measuredVoltage),
                'volt_input': self.inputVoltage,
                's2_volt_calibr': self.calibration}
        rsp = requests.post(ssrv_url + '/measures',
                            params={'sample_name': self.deviceAlId,
                                    'session_type': 's2_calib',
                                    'measure_type': 's2_volt_calibr',
                                    'station_name': self.stationName,
                                    'setup_name': self.setupName,
                                    'user_name': getpass.getuser()},
                            json={'data': data})
        rsp.raise_for_status()


class S2CurrentCalibrationCommand(BaseCommand):

    def __init__(self, device_al_id, voltmeter, s2_device,
                 station_name, setup_name):
        super(S2CurrentCalibrationCommand, self).__init__()
        self.deviceAlId = device_al_id
        self.vm = voltmeter
        self.s2 = s2_device
        self.measuredCurrent = []
        self.outputCurrentMeasuredRaw = []
        self.outputVoltageSetRaw = []
        self.inputVoltage = None
        self.calibration = None
        self.stationName = station_name
        self.setupName = setup_name

    def _execute(self):
        self.s2.reload_calibration()
        calibration = self.s2.calibration
        calibration.hardware_options |= 0x08  # disable the internal current limit
        self.s2.apply_calibration(calibration, store=False)
        self.s2.set_settings(pulse_period=1000, pulse_width=1000,
                             pulsing_mode='internal',
                             current_limit=100.0)
        self.s2.set_advanced_settings(output_voltage_set_raw=1,
                                      DCDC_mode=1)
        for i in range(650, 2000, 50):
            self.s2.set_advanced_settings(output_voltage_set_raw=i,
                                          DCDC_mode=1)
            sleep(1)

            measured_current = float(self.vm.query("MEAS:CURR:DC?"))
            self.s2.reload_info()
            self.s2.reload_settings()
            self.s2.reload_advanced_settings()

            self.measuredCurrent.append(measured_current)
            self.outputVoltageSetRaw.append(i)
            self.outputCurrentMeasuredRaw.append(self.s2.output_current_measured_raw)

            print("DAC={} ADC={:.2f} I={:.3f}".format(self.outputVoltageSetRaw[-1],
                                                      self.outputCurrentMeasuredRaw[-1],
                                                      self.measuredCurrent[-1]))
            if self.s2.status_label != S2_STATUS_OK:
                raise Exception('S2 status is not OK: {}'.format(self.s2.status_label))
            if self.outputCurrentMeasuredRaw[0] >= 4095:
                logger.warning('reached the maximum of the current measurement range')
                break
            if measured_current >= 3.0:
                logger.warning('reached max recommended average current for the S-2')
                break

        self.inputVoltage = self.s2.input_voltage_measured
        self.s2.set_advanced_settings(output_voltage_set_raw=1)
        self.shut_down()
        self.calibration = fit_curr_calibration(self.outputCurrentMeasuredRaw,
                                                self.measuredCurrent)
        self.store()

    def shut_down(self):
        self.s2.set_settings(voltage=0, pulsing_mode=S2_PULSING_OFF)
        self.s2.shut_down()

    def store(self):
        ssrv_url = gConfig2.get_url('ssrv_restless')
        data = {'curr_meas_raw': list(self.outputCurrentMeasuredRaw),
                'volt_set_raw': list(self.outputVoltageSetRaw),
                'curr_meas': list(self.measuredCurrent),
                'volt_input': self.inputVoltage,
                's2_curr_calibr': self.calibration}
        rsp = requests.post(ssrv_url + '/measures',
                            params={'sample_name': self.deviceAlId,
                                    'session_type': 's2_calib',
                                    'measure_type': 's2_curr_calibr',
                                    'station_name': self.stationName,
                                    'setup_name': self.setupName,
                                    'user_name': getpass.getuser()},
                            json={'data': data})
        rsp.raise_for_status()