# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
import logging

__author__ = 'chiesa'
__copyright__ = "Copyright Alpes Lasers SA"

import numpy as np

logger = logging.getLogger(__name__)


# noinspection PyTupleAssignmentBalance
def fit_volt_calibration(output_voltage_set_raw,
                         output_voltage_measured_raw,
                         measured_voltage):
    output_voltage_set_raw = np.array(output_voltage_set_raw)
    output_voltage_measured_raw = np.array(output_voltage_measured_raw)
    measured_voltage = np.array(measured_voltage)
    Vout_meas_params, vout_meas_res, _, _, _ = np.polyfit(output_voltage_measured_raw,
                                                          measured_voltage,
                                                          full=True,
                                                          deg=1)
    Vout_set_params, vout_set_res, _, _, _ = np.polyfit(measured_voltage,
                                                        output_voltage_set_raw,
                                                        full=True,
                                                        deg=1)
    return {'Vout_meas_a': Vout_meas_params[0],
            'Vout_meas_b': Vout_meas_params[1],
            'Vout_meas_res': vout_meas_res,
            'Vout_set_a': Vout_set_params[0],
            'Vout_set_b': Vout_set_params[1],
            'Vout_set_res': vout_set_res}


# noinspection PyTupleAssignmentBalance
def fit_curr_calibration(output_current_measured_raw,
                         measured_current):
    output_current_measured_raw = np.array(output_current_measured_raw)
    measured_current = np.array(measured_current)
    curr_params, curr_residual, _, _, _ = np.polyfit(output_current_measured_raw,
                                                     measured_current,
                                                     full=True,
                                                     deg=1)
    return {'I_a': curr_params[0],
            'I_b': curr_params[1],
            'I_res': curr_residual}