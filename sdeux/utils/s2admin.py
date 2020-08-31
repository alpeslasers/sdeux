# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
import requests
from configuration_manager import gConfig2
from requests.auth import HTTPBasicAuth

__author__ = 'chiesa'
__copyright__ = "Copyright Alpes Lasers SA"

s2admin = gConfig2.get_url('s2admin')

auth = HTTPBasicAuth(username='calibration_script',
                     password='924ht536g36tvSX')


def get_s2(device_id):
    rsp = requests.get(s2admin + '/api/s2',
                       params={'serial_number': device_id})
    rsp.raise_for_status()
    d = rsp.json()
    if not d:
        return None
    if len(d) == 1:
        return d[0]
    raise Exception('expected exactly one S2 device with device_id={}, but {} was found'.format(device_id, d))


def get_calibration(device_id):
    rsp = requests.get(s2admin + '/api/s2calibration',
                       params={'item__serial_number': device_id})
    rsp.raise_for_status()
    d = rsp.json()
    if not d:
        return None
    if len(d) == 1:
        return d[0]
    raise Exception('expected exactly one S2 calibration item with device_id={}, but {} was found'.format(device_id, d))


def update_s2_calibration(s2_calibration, s2_admin_calibration):
    s2_calibration.I_a = s2_admin_calibration['i_a']
    s2_calibration.I_b = s2_admin_calibration['i_b']
    s2_calibration.Vout_meas_a = s2_admin_calibration['vout_meas_a']
    s2_calibration.Vout_meas_b = s2_admin_calibration['vout_meas_b']
    s2_calibration.Vout_set_a = s2_admin_calibration['vout_set_a']
    s2_calibration.Vout_set_b = s2_admin_calibration['vout_set_b']
    s2_calibration.max



if __name__ == '__main__':
    get_s2(1)
