# -*- coding: utf-8 -*-
"""
Created by Olga Reinauer

Copyright 2019 Alpes Lasers SA, Saint-Blaise, Switzerland
"""

__author__ = 'olgare'
__copyright__ = "Copyright 2019, Alpes Lasers SA"

import logging
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

logger = logging.getLogger(__name__)


# Periodic signal is repeated 3 times
def generate_signal(signal_period, up_down_slices, n_repetitions):
    signal_y = ()
    for i in range(0, len(up_down_slices)):
        if i % 2 != 0:
            signal= np.zeros(up_down_slices[i])
        else:
            signal = np.ones(up_down_slices[i])
        signal_y= np.concatenate((signal_y, signal))
    signal_x_total= np.linspace(0, signal_period*n_repetitions, signal_period*n_repetitions)
    i=1
    signal_y_total=()
    while (i <= n_repetitions):
        signal_y_total = np.concatenate((signal_y_total, signal_y))
        i+=1
    return signal_x_total, signal_y_total


def calculate_duties(signal_x, signal_y, integration_time):
    total_up = []
    total_down = []
    duties=[]
    up=0
    down=0
    start = 0
    end = start + integration_time
    while (end < len(signal_x)-1):
        for i in range(start, end):
            if signal_y[i] == 0:
                down += 1
            else: up += 1
        total_up.append(up)
        total_down.append(down)
        start += 1
        end = start + integration_time
        up = 0
        down = 0
    for up in total_up:
        duties.append(float(up / integration_time))
    return duties


if __name__ == '__main__':
    period = 909
    up_down_slices_LW_A = [60, 30, 667, 152]
    x, y = generate_signal(period,  up_down_slices_LW_A, 3)
    duties= calculate_duties(x, y, 450)
    plt.plot(x, y, 'c', label='duty min: {:.2f} max:{:.2f}'.format(np.amin(duties), np.amax(duties)))
    plt.legend(loc='upper right')
    plt.xlabel('us')
    plt.show()
    sns.distplot(duties, label='duty cycle distribution')
    plt.legend()
    plt.show()





