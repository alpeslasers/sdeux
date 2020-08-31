import json
import time
from collections import OrderedDict
from copy import copy
from time import sleep

from dms import DMSManager
from configuration_manager import gConfig2
import logging


from sdeux.auto_detect import init_driver
from sdeux.communication import RETRY_NO
from sdeux.defs import S2_STATUS_OK
from sdeux.serial_handler import S2SerialHandler

from sdeux.s2Qualification.instruments.jura import Jura
from sdeux.s2Qualification.instruments.oscilloscope import Oscilloscope
from sdeux.s2Qualification.instruments.power_supply import PowerSupply
from sdeux.s2Qualification.instruments.multimeter import MultiMeter
from sdeux.s2Qualification.instruments.waveformgenerator import WaveFormGenerator
from sdeux.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from sdeux.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')
logger = logging.getLogger(__name__)


def power_reset(power_supply, s2):
    power_supply.set_voltage(0)
    sleep(5.0)
    power_supply.set_voltage(24.00)
    sleep(5.0)
    s2.set_up()
    sleep(5.0)
    s2.reset_overcurrent_flag()
    s2.reset_overvoltage_flag()
    s2.reset_undervoltage_flag()
    s2.reload_info()
    if not s2.status_label == 'ok':
        raise Exception('S2 is not OK: {}'.format(s2.status_label))


def reset_all(power_supply, s2, wfg):
    wfg.disable()
    sleep(2.0)
    power_reset(power_supply, s2)


def check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura):
    print('******************** Checking overcurrent for all pulsing modes *************')

    # Configure Measurement Internal
    report = OrderedDict()
    print('Internal Mode')
    reset_all(power_supply, s2, wfg)

    s2_settings = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=1000, current_limit=20,  current_limit_mode=1)
    s2.set_settings(**s2_settings, persistent = True)

    sleep(0.1)

    s2.reload_info()
    s2.reload_settings()

    report['mode_internal_s2_status'] = s2.status_label
    report['mode_internal_s2_output_current_limit'] = s2._settings.output_current_limit

    print('Mode A')
    reset_all(power_supply, s2, wfg)

    s2_settings = dict(pulsing_mode='modeA', voltage=8, pulse_period=1000, pulse_width=1000, current_limit=20, current_limit_mode=1)
    s2.set_settings(**s2_settings,  persistent = True)

    sleep(0.1)
    s2.reload_info()
    s2.reload_settings()

    report['modeA_status'] = s2.status_label
    report['modeA_s2_output_current_limit'] = s2._settings.output_current_limit

    print('Mode B')
    reset_all(power_supply, s2, wfg)

    s2_settings = dict(pulsing_mode='modeB', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20, current_limit_mode=1)
    s2.set_settings(**s2_settings,  persistent = True)
    sleep(0.1)
    s2.reload_info()
    s2.reload_settings()

    report['modeB_status'] = s2.status_label
    report['modeB_s2_output_current_limit'] = s2._settings.output_current_limit

    print('Mode CSS')
    reset_all(power_supply, s2, wfg)

    s2_settings = dict(pulsing_mode='modeCSS', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20, current_limit_mode=1)
    s2.set_settings(**s2_settings,  persistent = True)
    sleep(0.1)
    s2.reload_info()
    s2.reload_settings()

    report['modeCSS_status'] = s2.status_label
    report['modeCSS_s2_output_current_limit'] = s2._settings.output_current_limit

    print('Mode CST')
    reset_all(power_supply, s2, wfg)

    s2_settings = dict(pulsing_mode='modeCST', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20, current_limit_mode=1)
    s2.set_settings(**s2_settings,  persistent = True)
    sleep(0.1)
    s2.reload_info()
    s2.reload_settings()

    report['modeCST_status'] = s2.status_label
    report['modeCST_s2_output_current_limit'] = s2._settings.output_current_limit

    print('AB_A Mode')
    reset_all(power_supply, s2, wfg)
    s2_settings = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=None, current_limit=20,
                    voltage_A=8, voltage_B=5, pulse_width_A=1000, pulse_width_B=1000, current_limit_mode=1)
    s2.set_settings(**s2_settings,  persistent = True)
    sleep(0.1)

    jura.set_relays({'IN_ARM': 'OFF',
                     'IN_SAFETY': 'OFF',
                     'MCU_OUT_INT': 'OFF',
                     'INTERLOCK': 'OFF',
                     'IN_MOD_DIR': 'ON',
                     'GND': 'ON'})
    sleep(5.0)
    freq = 1000
    duty = 3
    oscillo.time_scale = 0.2 / freq
    wfg.set_settings(freq, duty, 1)
    sleep(2.0)
    wfg.enable_wfg()
    sleep(2.0)

    s2.reload_info()
    s2.reload_settings()
    report['mode_AB_A_s2_status'] = s2.status_label
    report['mode_AB_A_s2_output_current_limit'] = s2._settings.output_current_limit

    print('AB_B Mode')
    reset_all(power_supply, s2, wfg)

    s2_settings = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=None, current_limit=20,
                       voltage_A=8, voltage_B=5, pulse_width_A=1000, pulse_width_B=1000, current_limit_mode=1)
    s2.set_settings(**s2_settings, persistent = True )
    sleep(0.1)
    jura.set_relays({'IN_ARM': 'OFF',
                     'IN_SAFETY': 'OFF',
                     'MCU_OUT_INT': 'OFF',
                     'INTERLOCK': 'OFF',
                     'IN_MOD_DIR': 'ON',
                     'GND': 'ON'})
    sleep(5.0)
    freq = 1000
    duty = 80
    oscillo.time_scale = 0.2 / freq

    wfg.set_settings(freq, duty, 1)
    sleep(2.0)
    wfg.enable_wfg()
    sleep(2.0)
    s2.reload_settings()
    s2.reload_info()
    report['mode_AB_B_s2_status'] = s2.status_label
    report['mode_AB_B_s2_output_current_limit'] = s2._settings.output_current_limit

    return report


def pretty_print_report(report, expected):
    is_ok = True
    for k in report.keys():
        if 'status' in k:
            if (expected in k) and (report[k] != 'overcurrent'):
                is_ok = False
            elif report[k] != 'ok':
                is_ok = True
    if not is_ok:
        print('FAILED')
    else:
        print('OK')
    for k, v in report.items():
        print('{}: {}'.format(k, v))



def check_all_curr_limits(s2):

    print('******************** Configuring internal mode *************')
    try:
        conf = dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=0.1,
                    modea_limit=20, modeb_limit=20, modecst_limit=20, modecss_limit=20,
                    modeab_a_limit=20, modeab_b_limit=20)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info = get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                            "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'Internal'}
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> Internal Mode Check:')
        pretty_print_report(report, expected='internal')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))

    print('******************** Configuring mode A *************')
    try:
        conf = dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=20,
                             modea_limit=0.1, modeb_limit=20, modecst_limit=20, modecss_limit=20,
                             modeab_a_limit=20, modeab_b_limit=20)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info = get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                            "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'modeA'}
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> ModeA Check:')
        pretty_print_report(report, expected='modeA')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))

    print('******************** Configuring mode B *************')
    try:
        conf = dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=20,
                             modea_limit=20, modeb_limit=0.1, modecst_limit=20, modecss_limit=20,
                             modeab_a_limit=20, modeab_b_limit=20)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info = get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                            "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'modeB'}
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> ModeB Check:')
        pretty_print_report(report, expected='modeB')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))

    print('******************** Configuring mode CSS *************')
    try:
        conf=dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=20,
                             modea_limit=20, modeb_limit=20, modecst_limit=20, modecss_limit=0.1,
                             modeab_a_limit=20, modeab_b_limit=20)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info = get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                            "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'modeCSS'}
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> ModeCSS Check:')
        pretty_print_report(report, expected='modeCSS')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))

    print('******************** Configuring mode CST *************')
    try:
        conf=dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=20,
                             modea_limit=20, modeb_limit=20, modecst_limit=0.1, modecss_limit=20,
                             modeab_a_limit=20, modeab_b_limit=20)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info = get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                                 "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'modeCST'}
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> ModeCST Check:')
        pretty_print_report(report, expected='modeCST')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))

    print('******************** Configuring mode AB_limitA*************')
    try:
        conf=dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=20,
                             modea_limit=20, modeb_limit=20, modecst_limit=20, modecss_limit=20,
                             modeab_a_limit=0.1, modeab_b_limit=20)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info = get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                            "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'modeAB_A'}
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> ModeAB_A Check:')
        pretty_print_report(report, expected='modeAB')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))

    print('******************** Configuring mode AB_limitB*************')
    try:
        conf=dict(device_id=device_id, laser_id=laser_id, lasing_min_current=0, internal_limit=20,
                             modea_limit=20, modeb_limit=20, modecst_limit=20, modecss_limit=20,
                             modeab_a_limit=20, modeab_b_limit=0.1)
        s2.set_configuration(**conf)
        conf['laser_id'] = '{}'.format(laser_id)
        report = check_overcurrent_all_pulsing_modes(s2, power_supply, oscillo, wfg, jura)
        pulser_info =get_pulser_info(s2)
        pulser_info['laser_id'] = '{}'.format(laser_id)
        measurement_data = {"config": conf,
                            "report": report,
                            "pulser_info": json.dumps(pulser_info),
                            "test_scope": 'modeAB_B'
                            }
        save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_curr_lim")
        print('>>>> ModeAB_B Check:')
        pretty_print_report(report, expected='modeAB')
    except Exception as e:
        print('cannot apply this configuration, please check your firmware version: {}'.format(e))


if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()
    s2_th = S2SerialHandler('/dev/tty.CHIPIX-AL_FTV8G4AG')  # s2
    s2_th.open()
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')  #oscilloscope
    ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238_local')  #JURA
    ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')  #p ower supply
    wg_th = dms.get_instrument('HP/S2/INSTRUMENTS/AGILENT-WG')  #waveform generator
    mm_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200252')  # multimetrer K2000

    with dms.acquire_instruments(oscillo_th, ps_th, ju_th, wg_th, mm_th):
        oscillo = Oscilloscope(oscillo_th)
        power_supply = PowerSupply(ps_th)
        mm = MultiMeter(mm_th)
        jura = Jura(ju_th)
        s2 = None
        wfg = WaveFormGenerator(wg_th)
        try:
            # Configure JURA and POWER SUPPLY
            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'OFF'})
            power_supply.set_up()
            power_supply.set_voltage(24.00)
            sleep(5.0)

            # Initialize s2 and check if sample in DB
            s2 = init_driver(s2_th)
            s2.retry_policy = RETRY_NO
            s2.set_up()
            s2.reset_overcurrent_flag()
            s2.reload_info()
            if not s2.status_label == 'ok':
                raise Exception('S2 is not OK: {}'.format(s2.status_label))

            device_id = s2.info.device_id
            laser_id = s2.info.laser_id

            sleep(0.1)

            check_sample_in_db(get_s2_name(s2), get_s2_type(s2))

            # configure the time scale for MCU_OUT voltage measurement (0 or 3.3V)
            oscillo.set_settings(channel=4, volt_scale_chan=2, offset_chan=0, chan_trig=2, time_scale=3e-6)
            oscillo.drive()

            # *********************************************
            # Check current limits for each pulsing mode:
            # *********************************************

            oc_limits_triggered= check_all_curr_limits(s2)

        finally:
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            power_supply.release()
            jura.switch_all_off()
            s2_th.close()
            time_test_min = int((time.time() - st) / 60)
            time_test_sec = int((time.time() - st) % 60)
            print('Execution time is: {} min {} sec'.format(time_test_min, time_test_sec))
