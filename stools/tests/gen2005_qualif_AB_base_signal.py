import json
import time
from copy import copy
from time import sleep

from dms import DMSManager
from configuration_manager import gConfig2

from stools.auto_detect import init_driver
from stools.serial_handler import S2SerialHandler

from stools.s2Qualification.instruments.jura import Jura
from stools.s2Qualification.instruments.oscilloscope import Oscilloscope
from stools.s2Qualification.instruments.power_supply import PowerSupply
from stools.s2Qualification.instruments.multimeter import MultiMeter
from stools.s2Qualification.instruments.waveformgenerator import WaveFormGenerator
from stools.s2Qualification.measurement_scripts.mode_AB_pulsing import execute_AB_measurement
from stools.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from stools.utils.get_functions import get_s2_name, get_s2_type

ssrv_url = gConfig2.get_url('ssrv_restless')


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


if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()
    s2_th = S2SerialHandler('/dev/tty.CHIPIX-AL_FTV8G4AG') #s2
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

            # Initialize s2 and check if sample in DB
            s2 = init_driver(s2_th)
            s2.set_up()
            # s2.reload_info()
            check_sample_in_db(get_s2_name(s2), get_s2_type(s2))

            # configure the time scale for MCU_OUT voltage measurement (0 or 3.3V)
            oscillo.set_settings(channel=4, volt_scale_chan=2, offset_chan=0, chan_trig=2, time_scale=3e-6)
            oscillo.drive()
            reset_all(power_supply, s2, wfg)
            if not s2.status_label == 'ok':
                raise Exception('S2 is not OK: {}'.format(s2.status_label))
            # print(s2.configuration)
            sleep(1)
            s2config = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=None, current_limit=20,
                            voltage_A=5, voltage_B=2, pulse_width_A=1000, pulse_width_B=1000, current_limit_mode=0)
            s2.set_settings(**s2config)
            print(s2.settings)

            oscillo.set_settings(channel=1, volt_scale_chan=3, offset_chan=0, chan_trig=1, time_scale=5e-6)

            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'ON',
                             'GND': 'ON'})
            wfg_frequencies = [1000, 1000]
            wfg_dutys = [3, 90]
            for freq, duty in zip(wfg_frequencies, wfg_dutys):
                oscillo.time_scale = 0.0001
                wfg.set_settings(freq, duty, 1)
                wfg.enable_wfg()
                with open('debug.csv', 'w') as file:
                    for i in range(100):
                        debug_info = s2.query_debug_info()
                        file.write(debug_info)
                        file.write('\n')
                wg_info = '{}Hz_{}%'.format(freq, duty)
                oscillo.set_trig_type_pulse_width(3e-6, 150, 1000, 2, 'POS')
                sleep(2.0)
                data = execute_AB_measurement(s2, s2config, oscillo, power_supply, jura)
                oscillo.channel = 1
                data['test_scope'] = wg_info
                save_measurement(get_s2_name(s2), data)
                wfg.disable()

        finally:
            oscillo.cursor_position(0)  # position du curseur a 0 (delay)
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            power_supply.release()
            jura.switch_all_off()
            s2_th.close()
            time_test_min = int((time.time() - st) / 60)
            time_test_sec = int((time.time() - st) % 60)
            print('Execution time is: {} min {} sec'.format(time_test_min, time_test_sec))
