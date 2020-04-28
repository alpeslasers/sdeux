# -*- coding: utf-8 -*-
"""
Created by chiesa

Copyright Alpes Lasers SA, Switzerland
"""
import numpy
from matplotlib import pyplot as plt
from qualifix.calibr.analyze import fit_volt_calibration

__author__ = 'chiesa'
__copyright__ = "Copyright Alpes Lasers SA"


if __name__ == '__main__':
    volt_set_raw = numpy.array([1, 2, 3, 4, 5, 6])
    volt_meas_raw = numpy.array([3, 4, 6, 8, 10, 13])
    volt_meas = numpy.array([10.2, 12.3, 15.5, 16.3, 17.1, 18.6])
    calibr = fit_volt_calibration(output_voltage_set_raw=volt_set_raw,
                                  output_voltage_measured_raw=volt_meas_raw,
                                  measured_voltage=volt_meas)
    fig1 = plt.figure()
    ax1 = fig1.add_subplot(111)
    ax1.plot(volt_meas_raw, volt_meas)
    ax1.plot(volt_meas_raw, numpy.polyval([calibr['Vout_meas_a'],
                            calibr['Vout_meas_b']],
                           volt_meas_raw))
    fig2 = plt.figure()
    ax2 = fig2.add_subplot(111)
    ax2.plot(volt_meas, volt_set_raw)
    ax2.plot(volt_meas, numpy.polyval([calibr['Vout_set_a'],
                            calibr['Vout_set_b']],
                           volt_meas))
    plt.show()
