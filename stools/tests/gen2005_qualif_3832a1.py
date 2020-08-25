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
from stools.s2Qualification.measurement_scripts.Laser_output_ON import execute_laser_on_measurement
from stools.s2Qualification.measurement_scripts.mode_AB_pulsing import execute_AB_measurement
from stools.s2Qualification.measurement_scripts.mode_A_pulsing import execute_mode_A_measurement
from stools.s2Qualification.measurement_scripts.mode_B_pulsing import execute_mode_B_measurement
from stools.s2Qualification.measurement_scripts.mode_C_pulsing import execute_mode_C_measurement
from stools.s2Qualification.measurement_scripts.mode_internal_pulsing import execute_internal_measurement
from stools.s2Qualification.measurement_scripts.uptime_counters import execute_time_counters_measurement
from stools.s2Qualification.measurement_scripts.with_wfg_measurement import execute_wfg_measurement
from stools.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from stools.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--fw_rev', default='3832')
args = parser.parse_args()

if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()
    #s2_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-000')
    s2_th = S2SerialHandler('/dev/tty.usbserial-FTV8G4AG') #s2
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
            check_sample_in_db(get_s2_name(s2), get_s2_type(s2))

            # configure the time scale for MCU_OUT voltage measurement (0 or 3.3V)
            oscillo.set_settings(channel=4, volt_scale_chan=2, offset_chan=0, chan_trig=2, time_scale=3e-6)
            oscillo.drive()


            # Configure Measurement Internal
            print('Internal Measurement')
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=15000, pulse_width=300, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement 1Mhz
            s2config = dict(pulsing_mode='internal', voltage=8, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=4, offset_chan=0, chan_trig=2, time_scale=0.2e-6)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Current measurement
            s2config = dict(pulsing_mode='internal', voltage=2, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=4, offset_chan=0, chan_trig=2, time_scale=0.2e-6)
            sleep(5.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            data["test_scope"] = 'MeasCur_'
            data["current_multimeter"] = mm.get_current()
            save_measurement(get_s2_name(s2), data)

            # Perform lasing counter tests
            # Operation and lasing counters should increase
            start_time = time.time()
            initial_uptime = s2.get_uptime()
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=15000, pulse_width=300, current_limit=20)
            s2.set_settings(**s2config)
            time.sleep(5)
            end_time = time.time()
            final_uptime = s2.get_uptime()
            data = execute_time_counters_measurement(s2, s2config, power_supply, jura, initial_uptime, final_uptime,
                                                     start_time, end_time)
            save_measurement(get_s2_name(s2), data)

            # Operation counter inactive, lasing counter active
            start_time = time.time()
            initial_uptime = s2.get_uptime()
            s2config = dict(pulsing_mode='internal', voltage=4, pulse_period=15000, pulse_width=300, current_limit=20)
            s2.set_settings(**s2config)
            time.sleep(5)
            end_time = time.time()
            final_uptime = s2.get_uptime()
            data = execute_time_counters_measurement(s2, s2config, power_supply, jura, initial_uptime, final_uptime,
                                                     start_time, end_time)
            save_measurement(get_s2_name(s2), data)

            # Operation counter inactive, lasing counter inactive
            start_time = time.time()
            initial_uptime = s2.get_uptime()
            s2config = dict(pulsing_mode='internal', voltage=0, pulse_period=15000, pulse_width=300, current_limit=20)
            s2.set_settings(**s2config)
            time.sleep(5)
            end_time = time.time()
            final_uptime = s2.get_uptime()
            data = execute_time_counters_measurement(s2, s2config, power_supply, jura, initial_uptime, final_uptime,
                                                     start_time, end_time)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeA
            s2config = dict(pulsing_mode='modeA', voltage=8, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=250e-6)
            sleep(2.0)
            data = execute_mode_A_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeB
            s2config = dict(pulsing_mode='modeB', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=200e-6)
            sleep(2.0)
            data = execute_mode_B_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeCSS
            s2config = dict(pulsing_mode='modeCSS', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=2e-3)
            sleep(2.0)
            data = execute_mode_C_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeCST
            s2config = dict(pulsing_mode='modeCST', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=2.5e-3)
            sleep(2.0)
            data = execute_mode_C_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement laser on
            s2config = dict(pulsing_mode='internal', voltage=6, pulse_period=10000, pulse_width=3000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=3, volt_scale_chan=2, offset_chan=0, chan_trig=3, time_scale=3e-6)
            sleep(2.0)
            data = execute_laser_on_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement Internal overcurrent
            print('Overcurrent test')
            s2.reload_bit_stats()
            bit_results_before = copy(s2.bit_stats)
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=1000, current_limit=1)
            s2.set_settings(**s2config)
            total_uptime = s2.get_uptime().total_uptime
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            s2.reload_bit_stats()
            bit_results_after = s2.bit_stats
            print('BIT before: ' + str(bit_results_before))
            print('BIT after: ' + str(bit_results_after))
            data["test_scope"] = 'OvCur_'
            data["bit_results_before"] = json.dumps(bit_results_before.to_dict())
            data["bit_results_after"] = json.dumps(bit_results_after.to_dict())
            data["total_uptime"] = total_uptime
            save_measurement(get_s2_name(s2), data)
            s2.reset_overcurrent_flag()
            power_supply.set_voltage(0)
            power_supply.set_voltage(24.00)

            # Configure Power Supply 9 to 25V
            s2config = dict(pulsing_mode='internal', voltage=8, pulse_period=1000, pulse_width=400,
                            current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=4, offset_chan=0, chan_trig=2, time_scale=0.2e-6)
            for PowerSupplyVoltage in range(9, 26, 1):
                power_supply.set_voltage(PowerSupplyVoltage)
                sleep(2.0)
                data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
                data["test_scope"] = 'supply_{:.1f}V_'.format(PowerSupplyVoltage)
                save_measurement(get_s2_name(s2), data)
            power_supply.set_voltage(24.00)

            # Configure Measurement Internal undervoltage
            print('Undervoltage test')
            s2.reload_bit_stats()
            bit_results_before = copy(s2.bit_stats)
            total_uptime = s2.get_uptime().total_uptime
            power_supply.set_voltage(5.00)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            s2.reload_bit_stats()
            bit_results_after = s2.bit_stats
            print('BIT before: ' + str(bit_results_before))
            print('BIT after: ' + str(bit_results_after))
            data["test_scope"] = 'UnVolt_'
            data["bit_results_before"] = json.dumps(bit_results_before.to_dict())
            data["bit_results_after"] = json.dumps(bit_results_after.to_dict())
            data["total_uptime"] = total_uptime
            save_measurement(get_s2_name(s2), data)

            power_supply.set_voltage(15.00)
            s2.reset_undervoltage_flag()

            s2.reload_info()

            # Configure Measurement Internal overvoltage
            print('Overvoltage test')
            s2.reload_bit_stats()
            bit_results_before = copy(s2.bit_stats)
            total_uptime = s2.get_uptime().total_uptime
            power_supply.set_voltage(28.10)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            s2.reload_bit_stats()
            power_supply.set_voltage(24.0)
            bit_results_after = s2.bit_stats
            print('BIT before: ' + str(bit_results_before))
            print('BIT after: ' + str(bit_results_after))
            data["test_scope"] = 'OvVolt_'
            data["bit_results_before"] = json.dumps(bit_results_before.to_dict())
            data["bit_results_after"] = json.dumps(bit_results_after.to_dict())
            data["total_uptime"] = total_uptime
            save_measurement(get_s2_name(s2), data)

            power_supply.set_voltage(24.00)
            s2.reset_overvoltage_flag()

            # Configure Measurement modeAB
            s2config = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=None, current_limit=20,
                            voltage_A=8, voltage_B=5, pulse_width_A=1000, pulse_width_B=1000)
            s2.set_settings(**s2config)

            oscillo.set_settings(channel=1, volt_scale_chan=3, offset_chan=0, chan_trig=1, time_scale=5e-6)
            jura.set_relays({'IN_ARM': 'OFF',
                            'IN_SAFETY': 'OFF',
                            'MCU_OUT_INT': 'OFF',
                            'INTERLOCK': 'OFF',
                            'IN_MOD_DIR': 'ON',
                            'GND': 'ON'})
            if args.fw_rev == '3832':
                wfg_frequencies = [1000, 1000, 4000, 4000, 16]
                wfg_dutys = [3, 80, 40, 96, 81]
            else:
                wfg_frequencies = [16, 16, 16, 1000, 1000, 4000, 4000, 16]
                wfg_dutys = [0.01, 10, 16, 3, 80, 40, 96, 81]
            iiii = 0
            for freq, duty in zip(wfg_frequencies, wfg_dutys):
                oscillo.time_scale = 0.2 / freq
                wfg.set_settings(freq, duty, 1)
                wfg.enable_wfg()
                wg_info = '{}Hz_{}%'.format(freq, duty)
                sleep(2.0)
                data = execute_AB_measurement(s2, s2config, oscillo, power_supply, jura)
                oscillo.channel = 1
                data['test_scope'] = wg_info
                save_measurement(get_s2_name(s2), data)
                if iiii == 0:
                    wfg.disable()
                    data = execute_AB_measurement(s2, s2config, oscillo, power_supply, jura)
                    data['test_scope'] = 'wg_OFF'
                    save_measurement(get_s2_name(s2), data)
                    oscillo.channel = 1
                    iiii += 1

            # Configure Measurement modeAB check pulse width pulse_width_A et pulse_width_B
            s2config = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=None, current_limit=20,
                            voltage_A=8, voltage_B=5, pulse_width_A=300, pulse_width_B=500)
            s2.set_settings(**s2config)

            oscillo.set_settings(channel=1, volt_scale_chan=3, offset_chan=0, chan_trig=1, time_scale=5e-6)

            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'ON',
                             'GND': 'ON'})
            wfg_frequencies = [1000, 1000]
            wfg_dutys = [3, 80]
            for freq, duty in zip(wfg_frequencies, wfg_dutys):
                oscillo.time_scale = 500e-9 #choix pour voir les pulses correctement
                wfg.set_settings(freq, duty, 1)
                wfg.enable_wfg()
                wg_info = '{}Hz_{}%'.format(freq, duty)
                oscillo.set_trig_type_pulse_width(3e-6, 150, 1000, 2, 'POS')
                sleep(2.0)
                data = execute_AB_measurement(s2, s2config, oscillo, power_supply, jura)
                oscillo.channel = 1
                if duty < 25:
                    data['duty_cycle'] = round(s2config['pulse_width_A'] / s2config['pulse_period'], 2)
                elif duty > 30:
                    data['duty_cycle'] = round(s2config['pulse_width_B'] / s2config['pulse_period'], 2)

                data['test_scope'] = wg_info
                save_measurement(get_s2_name(s2), data)

            oscillo.cursor_position(0) # position du curseur a 0 (delay)

            # =========================== INTERLOCKS ===================================================================
            # IN ARM ON
            jura.set_relays({'IN_ARM': 'ON',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'ON'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=1, volt_scale_chan=3, offset_chan=0, chan_trig=1, time_scale=2e-3)

            wfg.set_settings(frequency=100, duty=80, output=1)
            wfg.enable_wfg()
            time.sleep(2)
            data = execute_wfg_measurement(s2, s2config, oscillo, power_supply, jura, second_channel=2)
            data['test_scope'] = 'IN_ARM_'
            wfg.disable()
            save_measurement(get_s2_name(s2), data)

            # IN ARM ON delay measurement
            jura.set_relays({'IN_ARM': 'ON',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'ON'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=1, volt_scale_chan=3, offset_chan=0, chan_trig=1, time_scale=100e-9)

            wfg.set_settings(frequency=100, duty=80, output=1)
            wfg.enable_wfg()
            time.sleep(2)
            data = execute_wfg_measurement(s2, s2config, oscillo, power_supply, jura, second_channel=2)
            data['test_scope'] = 'IN_ARM_'
            time.sleep(2)
            delay = oscillo.get_delay(1, 2)
            data["pulse_delay"] = delay
            wfg.disable()
            save_measurement(get_s2_name(s2), data)

            # IN SAFETY ON
            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'ON',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'ON'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=1, volt_scale_chan=4, offset_chan=0, chan_trig=1, time_scale=2e-3)

            wfg.set_settings(frequency=100, duty=80, output=1)
            wfg.enable_wfg()
            time.sleep(2)
            data = execute_wfg_measurement(s2, s2config, oscillo, power_supply, jura, second_channel=2)
            data['test_scope'] = 'IN_SAFETY_'
            wfg.disable()
            save_measurement(get_s2_name(s2), data)

            # MCU_OUT_INT ON
            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'ON',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'OFF'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=0.05)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            data['test_scope'] = 'MCU_OUT_'
            save_measurement(get_s2_name(s2), data)

            # INTERLOCK ON
            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'ON',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'OFF'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=50e-9)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            data['test_scope'] = 'INTERLOCK_'
            save_measurement(get_s2_name(s2), data)

            # IN_ARM IN_SAFETY ON
            jura.set_relays({'IN_ARM': 'ON',
                             'IN_SAFETY': 'ON',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'ON'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=50e-9)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            data['test_scope'] = 'IN_ARM_SAFETY_'
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement Internal
            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'OFF'})
            sleep(5)
            s2config = dict(pulsing_mode='internal', voltage=5, pulse_period=15000, pulse_width=1500, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            sleep(2.0)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

        finally:
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            power_supply.release()
            jura.switch_all_off()
            s2_th.close()
            time_test_min = int((time.time() - st) / 60)
            time_test_sec = int((time.time() - st) % 60)
            print('Execution time is: {} min {} sec'.format(time_test_min, time_test_sec))
