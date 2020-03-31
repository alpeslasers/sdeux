# -*- coding: utf-8 -*-
"""
Created by gregory on 19.08.16

Copyright 2016 Alpes Lasers SA, Neuchatel, Switzerland
"""

import json
import math
import logging
import time
import threading

from pirata.drivers.base import BaseDriver
from pirata.utils.synchronize import synchronized
from pirata.drivers.S2.exceptions import (S2InvalidPulseParamsError, S2InvalidVoltageError, S2OvercurrentError,
                                          S2UndervoltageError)

logger = logging.getLogger(__name__)

__author__ = 'gregory'
__copyright__ = "Copyright 2016, Alpes Lasers SA"


class S2(BaseDriver):
    """Driver to control the S2 via a RPC s2_py_server.

    The overriding server is there for testing purposes only: it bypasses the DMS instrument locking mechanism and as
    such is unsafe.
    """

    @property
    def server(self):
        return self.overriding_server if self.overriding_server is not None else self.th

    @property
    def applied_voltage(self):
        return self._settings['applied_voltage']

    def __init__(self, th, overriding_server=None):
        super(S2, self).__init__(th)
        self.overriding_server = overriding_server
        self._settings = {}
        self._info = {}
        self._myLock = threading.RLock()
        self._last_info_time = 0
        self._set_settings_time = 0
        self.max_voltage_step = 0.4  # Voltage step used for the ramping
        self.voltage_ramp_speed = 2.0  # voltage speed in [V/s] used for the ramping

    @synchronized
    def set_up(self, config_name=None):
        """Sets up, clears potential overcurrent flags."""
        self.server.s2_reset_overcurrent_flag()
        self._settings = json.loads(self.server.s2_get_settings())
        self._info = json.loads(self.server.s2_get_info())

    @synchronized
    def shut_down(self):
        """Shuts down, stops s2 output"""
        self.set_settings(pulsing_mode='off')

    @synchronized
    def reset_overcurrent_flag(self):
        self.server.s2_reset_overcurrent_flag()

    def get_pulse_modes(self):
        return ['internal', 'modeA', 'modeB', 'modeCSS',
                'modeCST', 'modeB4', 'modeB6', 'modeB8', 'burst_mode']

    @synchronized
    def set_settings(self, pulsing_mode=None, voltage=None, pulse_period=None,
                     pulse_width=None, current_limit=None, force=False,
                     burst_ON=None, burst_OFF=None):
        """Set the specified settings. The unspecified parameters (=None) are not changed. Ramps up or down slowly the
        applied voltage"""
        was_off = self._settings['pulsing_mode'] == 'off'
        previous_voltage = self._settings['applied_voltage'] if not was_off else 0.0
        if pulsing_mode is None:
            pulsing_mode = self._settings['pulsing_mode']

        if voltage is not None:
            if (not force) and (not self._info['voltage_min'] <= voltage <= self._info['voltage_max']):
                raise S2InvalidVoltageError('Voltage {} out of bounds ({}, {})'.format(voltage, self._info['voltage_min'],
                                                                            self._info['voltage_max']))
            self._settings['applied_voltage'] = voltage
        if pulse_period is not None:
            if (not force) and (not self._info['period_min'] <= pulse_period <= self._info['period_max']):
                raise S2InvalidPulseParamsError('Pulse period {} out of bounds ({}, {})'.format(pulse_period, self._info['period_min'],
                                                                                                self._info['period_max']))
            self._settings['pulse_period'] = pulse_period
        if pulse_width is not None:
            if (not force) and (not self._info['pulse_width_min'] <= pulse_width <= self._info['pulse_width_max']):
                raise S2InvalidPulseParamsError('Pulse width {} out of bounds ({}, {})'.format(pulse_width,
                                                                                               self._info['pulse_width_min'],
                                                                                               self._info['pulse_width_max']))
            self._settings['pulse_width'] = pulse_width
        if current_limit is not None:
            self._settings['current_limit'] = current_limit

        # Ramping of the voltage.
        shut_down = pulsing_mode == 'off'
        target_voltage = self._settings['applied_voltage'] if not shut_down else 0.0
        applied_voltage = previous_voltage
        if was_off:
            self._settings['pulsing_mode'] = pulsing_mode

        while abs(applied_voltage - target_voltage) > self.max_voltage_step:
            applied_voltage += math.copysign(self.max_voltage_step, target_voltage - applied_voltage)
            self._settings['applied_voltage'] = applied_voltage
            self.server.s2_set_settings(json.dumps(self._settings))
            time.sleep(self.max_voltage_step / self.voltage_ramp_speed)

        # Final set
        self._settings['applied_voltage'] = target_voltage
        self._settings['pulsing_mode'] = pulsing_mode
        self._settings['burst_ON'] = burst_ON
        self._settings['burst_OFF'] = burst_OFF

        self._set_settings_time = time.time()
        self.server.s2_set_settings(json.dumps(self._settings))

        return self._settings
    
    def whoareyou(self):
        info = self.get_info()
        return 'S2: device_id={0}, soft_version={1}, hard_version={2}'.format(info.get('device_id'),
                                                                              info.get('sw_version'),
                                                                              info.get('hw_version'))

    @synchronized
    def get_info(self):
        """Returns the current info. WARNING: the S2 only refreshes so often. Calling this
        method twice in a row will likely produce the same result"""
        self._info = json.loads(self.server.s2_get_info())
        return self._info

    @synchronized
    def get_settings(self):
        """Returns the settings dictionary (applied_voltage, pulse parameters, ...)"""
        self._settings = json.loads(self.server.s2_get_settings())
        return self._settings

    @synchronized
    def get_status(self):
        return self.server.get_status()

    def get_measure(self, immediate=False):
        """Returns a tuple (current, voltage). Raises an exception if the S2 status is overcurrent or undervoltage.

        :param immediate: If False (default), the method waits until the signal is stabilized by waiting a fixed amount
        of time set by the S2 driver (signal_stabilization_sec) since the last set_settings call.
        If True, performs the measurement immediately, regardless of the time of the last set_settings call."""
        delta = time.time() - self._set_settings_time - self._info['signal_stabilization_sec']
        if delta < 0 and not immediate:
            time.sleep(-delta)
        s2i = self.get_info()
        status = s2i['status']
        if status == 'undervoltage':
            raise S2UndervoltageError()
        if status == 'overcurrent':
            raise S2OvercurrentError()

        return s2i['measured_current'], s2i['measured_voltage']

    @synchronized
    def enable_quiet_mode(self):
        return self.server.enable_quiet_mode()

    @synchronized
    def disable_quiet_mode(self):
        return self.server.disable_quiet_mode()


if __name__ == '__main__':
    from dms import DMSManager
    with DMSManager() as dms:
        # s2 = S2(dms.get_instrument('PROD/AGEING/INSTRUMENTS/S2_1'))
        s2 = S2(dms.get_instrument('PROD/DUE/INSTRUMENTS/S2_RED'))
        with dms.acquire_instruments(s2):
            s2.set_up()
            s2.set_settings('off', pulse_period=500)