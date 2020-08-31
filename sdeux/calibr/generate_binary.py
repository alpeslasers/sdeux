#!/usr/bin/env python3

import argparse
import getpass
from termcolor import cprint
from pyfiglet import figlet_format
import os.path
import shutil
from time import sleep
import serial
import numpy as np
import scipy.stats

import coloredlogs
import logging
from logging.handlers import RotatingFileHandler

from s2_py import serial_open, serial_close, s2_serial_setup, \
    S2_API_VERSION, NULL, S2_BAUD, TIMEOUT_RX, \
    s2_reboot_to_bootloader, \
    S2_info, s2_query_info, \
    S2_settings, s2_set_settings, \
    S2_calibration, s2_query_calibration, s2_set_calibration, \
    S2_uptime, s2_query_uptime, \
    S2_advanced_settings, s2_set_advanced_settings, \
    S2_advanced_info, s2_query_advanced_info, \
    s2_reset_status_flag, S2_STATUS_OVERCURRENT, \
    S2_debug, S2_PACKET_DEBUG_INFO, \
    S2_PULSING_INTERNAL, S2_PULSING_OFF, \
    ffi, s2_exchange

from sdeux.calibr import s2_cal_db
from sdeux.calibr.s2_local_settings import s2_port_name, keithley_port_name


logging.basicConfig()
log = logging.getLogger('s2')
coloredlogs.install(level='INFO', logger=log)
log_formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
usr_name = getpass.getuser()
log_rfh = RotatingFileHandler('s2_log_{}.txt'.format(usr_name), maxBytes=1e6, backupCount=5)
log_rfh.setFormatter(log_formatter)
log.addHandler(log_rfh)


def inform(text, *args):
    term_width = shutil.get_terminal_size()[0]
    cprint(figlet_format(text, font='starwars', width=term_width),
           *args, attrs=['bold'])


def check(ret):
    if ret != 0:
        log.error('communication problem: {}'.format(ret))
        exit(1)
    return ret


def query_uptimes(s2port):
    s2u = S2_uptime()
    check(s2_query_uptime(s2port, s2u))
    log.info('uptime: {} s, total uptime: {} s'.format(s2u.uptime, s2u.total_uptime))


def poll_debug_info(s2port):
    s2d = S2_debug()
    while True:
        check(s2_exchange(s2port, S2_PACKET_DEBUG_INFO, NULL, 0,
                          S2_PACKET_DEBUG_INFO, s2d, ffi.sizeof(s2d[0]), TIMEOUT_RX))
        log.info(ffi.string(s2d.output))
        sleep(.02)


def poll_currents(s2port):
    s2i = S2_info()
    s2ai = S2_advanced_info()
    while True:
        check(s2_query_info(s2port, s2i))
        check(s2_query_advanced_info(s2port, s2ai))
        log.info("{:.3f}\t{:.3f}\t{:.2f}".format(s2ai.output_current_measured_raw,
                                                  s2ai.current_out_of_pulse_raw, s2i.output_current_measured))
        sleep(.02)


def connect_keithley():
    k_port = serial.Serial(keithley_port_name, 9600, timeout=1) #11 mars 2019 change 19200 to 9600
    k_port.write("*IDN?\n".encode('UTF-8'))
    mm_id = k_port.readline()
    log.info(mm_id)
    assert mm_id.startswith(b'KEITHLEY INSTRUMENTS INC.,MODEL 2000,')
    return k_port


def write_calibration_and_options(s2port, db_cal, db_board):
    s2c = S2_calibration()
    c = db_cal

    s2c.I_a = c['i_a']
    s2c.I_b = c['i_b']
    s2c.Vout_meas_a = c['vout_meas_a']
    s2c.Vout_meas_b = c['vout_meas_b']
    s2c.Vout_set_a = c['vout_set_a']
    s2c.Vout_set_b = c['vout_set_b']
    s2c.hardware_options = db_board['hw_opts']
    s2c.max_peak_current = c['max_measurable_current']
    check(s2_set_calibration(s2port, s2c, True))


def main():
    username = getpass.getuser()

    inform("HELLO {} !".format(username))
    inform("LET'S PLAY S2 !!!")

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=s2_port_name)
    parser.add_argument("--boot", action='store_const', const=True, default=False)
    parser.add_argument("--rewrite", action='store_const', const=True, default=False)
    parser.add_argument("--reset", choices=['uptimes', 'overcurrent', 'settings'])
    parser.add_argument("--calibrate", choices=['current', 'voltage'])
    parser.add_argument("--poll", choices=['debug', 'currents'])
    args = parser.parse_args()

    log.info('using port {}'.format(args.port))
    if not os.path.exists(args.port):
        log.error('serial port does not exist')
        exit(1)

    s2port = serial_open(args.port.encode())
    if s2port == NULL:
        log.error('problem opening serial port')
        exit(1)

    ret = s2_serial_setup(s2port, S2_BAUD)
    if ret != 0:
        log.error('error setting up serial port')
        exit(ret)

    s2i = S2_info()
    check(s2_query_info(s2port, s2i))
    log.info('connected')
    log.info('hardware version: {}'.format(s2i.hw_version))
    log.info('device ID: {}'.format(s2i.device_id))
    log.info('api version: {}'.format(s2i.API_version))
    log.info('firmware version: {}'.format(s2i.sw_version))

    db_board = s2_cal_db.get_board(s2i.device_id)
    if db_board is None:
        db_board = s2_cal_db.create_board(s2i.device_id)
        log.info('the board was not in the database - added it')
    db_board['hardware_revision'] = s2i.hw_version
    db_board['firmware_version'] = str(s2i.sw_version)
    s2_cal_db.write_board(db_board)
    log.info('updated the board information in the database')

    # if s2i.API_version != S2_API_VERSION:
    #     log.error('incompatible API version: {} on the board, {} in this script'.format(s2i.API_version, S2_API_VERSION))
    #     exit(1)

    query_uptimes(s2port)

    db_calibration = s2_cal_db.get_calibration(s2i.device_id)
    if db_calibration is None:
        log.info('no calibration for this board in the database')
        # TODO: propose to calibrate

    s2c = S2_calibration()
    check(s2_query_calibration(s2port, s2c))
    log.info('max peak current: {}, hw options: {}'.format(s2c.max_peak_current,
                                                            s2c.hardware_options))

    if args.boot:
        log.info('rebooting to bootloader')
        ret = check(s2_reboot_to_bootloader(s2port))
        inform('done')
        exit(ret)

    if args.rewrite:
        log.info('rewriting calibration')
        write_calibration_and_options(s2port, db_calibration, db_board)

    if args.reset == 'uptimes':
        s2as = S2_advanced_settings()
        s2as.flag_reset_uptime = 0xAA00BCD0
        sleep(.5)
        check(s2_set_advanced_settings(s2port, s2as))
        log.info('uptimes reset')
        sleep(.5)
        query_uptimes(s2port)

    if args.reset == 'overcurrent':
        check(s2_reset_status_flag(s2port, S2_STATUS_OVERCURRENT))
        log.info('overcurrent reset')
        # TODO: read flags

    if args.reset == 'settings':
        s2s = S2_settings()  # all fields already have default values assigned in constructor
        check(s2_set_settings(s2port, s2s, True))
        log.info('settings reset')

    if args.calibrate == 'voltage':
        s2s = S2_settings()
        s2as = S2_advanced_settings()
        s2ai = S2_advanced_info()

        s2s.pulse_period = 100  # DC mode
        s2s.pulse_width = 100
        s2s.pulsing_mode = S2_PULSING_INTERNAL
        s2s.output_voltage_set = 1.0
        s2s.output_current_limit = 10
        check(s2_set_settings(s2port, s2s, False))

        s2as.output_voltage_set_raw = 1
        s2as.DCDC_mode = 1
        check(s2_set_advanced_settings(s2port, s2as))

        k_port = connect_keithley()
        out = []
        sleep(2)

        log.info("DAC - ADC - voltage")
        # TODO: switch the output off on any fail
        for i in range(650, 4095, 50):
            s2as.output_voltage_set_raw = i
            check(s2_set_advanced_settings(s2port, s2as))

            sleep(1)

            k_port.write("MEAS:VOLT:DC?\n".encode('UTF-8'))
            x = float(k_port.readline()[:-1])

            check(s2_query_advanced_info(s2port, s2ai))
            check(s2_query_info(s2port, s2i))

            res = i, s2ai.output_voltage_measured_raw, x
            out.append(res)
            log.info("{} {:.2f} {:.3f}".format(*res))
            if s2i.status != 0:
                log.warning('S2 status is not OK: {}'.format(s2i.status))
                s2s.output_voltage_set = 0
                s2s.pulsing_mode = S2_PULSING_OFF
                check(s2_set_settings(s2port, s2s, False))
                exit(1)

        s2as.output_voltage_set_raw = 1  # 0 will be ignored by the firmware :)
        check(s2_set_advanced_settings(s2port, s2as))

        s2s.pulsing_mode = S2_PULSING_OFF
        check(s2_set_settings(s2port, s2s, False))

        DAC, ADC, V = np.array(out).T
        s2c.Vout_meas_a, s2c.Vout_meas_b, r_value1, _, _ = scipy.stats.linregress(ADC, V)
        s2c.Vout_set_a, s2c.Vout_set_b, r_value2, _, _ = scipy.stats.linregress(V, DAC)
        log.info('Vout_meas_a={}\nVout_meas_b={}'.format(s2c.Vout_meas_a, s2c.Vout_meas_b, r_value1))
        log.info('Vout_set_a={}\nVout_set_b={}'.format(s2c.Vout_set_a, s2c.Vout_set_b, r_value2))
        log.info('R: {}, {}'.format(r_value1, r_value2))
        if r_value1 < 0.99 or r_value2 < 0.99:
            log.warning('The calibration is not very precise!')

        c = s2_cal_db.get_calibration(s2i.device_id)
        if c is None:
            c = s2_cal_db.create_calibration(s2i.device_id)
            log.info('added new calibration into the database')
        c['vout_meas_a'] = s2c.Vout_meas_a
        c['vout_meas_b'] = s2c.Vout_meas_b
        c['vout_set_a'] = s2c.Vout_set_a
        c['vout_set_b'] = s2c.Vout_set_b
        c['calibrated_at'] = s2i.input_voltage_measured
        s2_cal_db.write_calibration(c)

        check(s2_set_calibration(s2port, s2c, True))

        log.info('done')

    if args.calibrate == 'current':
        s2ai = S2_advanced_info()
        s2as = S2_advanced_settings()
        s2c = S2_calibration()
        s2s = S2_settings()

        c = s2_cal_db.get_calibration(s2i.device_id)
        if c is None:
            log.error('No calibration for this board found in the database. '
                      'The voltage calibration has to be done first.')
            exit(1)

        k_port = connect_keithley()

        s2c.hardware_options |= 0x08  # disable the internal current limit
        check(s2_set_calibration(s2port, s2c, False))

        s2s.pulse_period = 100
        s2s.pulse_width = 100
        s2s.pulsing_mode = S2_PULSING_INTERNAL
        s2s.output_current_limit = 100
        check(s2_set_settings(s2port, s2s, False))  # set settings, without persistence

        s2as.output_voltage_set_raw = 1
        s2as.DCDC_mode = 1
        check(s2_set_advanced_settings(s2port, s2as))

        out = []
        for i in range(650, 2000, 50):
            s2as.output_voltage_set_raw = i
            check(s2_set_advanced_settings(s2port, s2as))

            sleep(1)

            k_port.write("MEAS:CURR:DC?\n".encode('UTF-8'))
            x = float(k_port.readline()[:-1])

            check(s2_query_info(s2port, s2i))
            check(s2_query_advanced_info(s2port, s2ai))

            res = s2ai.output_current_measured_raw, x
            if res[0] >= 4095:
                log.warning('reached the maximum of the current measurement range')
                break
            if x >= 3.0:
                log.warning('reached max recommended average current for the S-2')
                break
            out.append(res)
            log.info("{} ".format(i) + "{:.2f} {:.3f}".format(*res))
            if s2i.status != 0:
                log.warning('S2 status is not OK: {}'.format(s2i.status))
                s2s.output_voltage_set = 0
                s2s.pulsing_mode = S2_PULSING_OFF
                check(s2_set_settings(s2port, s2s, False))
                exit(1)

        s2s.output_voltage_set = 0
        s2s.pulsing_mode = S2_PULSING_OFF
        check(s2_set_settings(s2port, s2s, False))

        check(s2_query_calibration(s2port, s2c))

        ADC, I = np.array(out).T
        s2c.I_a, s2c.I_b, r_value, p_value, std_err = scipy.stats.linregress(ADC, I)
        log.info('multiplier = {};\noffset = {};\nR={}'.format(s2c.I_a, s2c.I_b, r_value))
        if r_value < 0.99:
            log.warning('The calibration is not very precise!')

        c['i_a'] = s2c.I_a
        c['i_b'] = s2c.I_b
        c['calibrated_at'] = s2i.input_voltage_measured
        s2_cal_db.write_calibration(c)

        # fetch it back to get the calculated maximum current value
        c = s2_cal_db.get_calibration(s2i.device_id)
        db_board = s2_cal_db.get_board(s2i.device_id)
        s2c.max_peak_current = c['max_measurable_current']
        s2c.hardware_options = db_board['hw_opts']
        log.info('max measurable value: {}'.format(s2c.max_peak_current))
        check(s2_set_calibration(s2port, s2c, True))
        log.info('done')

    if args.poll == 'debug':
        poll_debug_info(s2port)

    if args.poll == 'currents':
        poll_currents(s2port)

    log.info('done')
    inform("that's it")


if __name__ == '__main__':
    main()
