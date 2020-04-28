import time
from dms import DMSManager
from configuration_manager import gConfig2

from stools.auto_detect import init_driver

from stools.s2Qualification.instruments.jura import Jura
from stools.s2Qualification.instruments.oscilloscope import Oscilloscope
from stools.s2Qualification.instruments.power_supply import PowerSupply
from stools.s2Qualification.instruments.waveformgenerator import WaveFormGenerator
from stools.s2Qualification.measurement_scripts.Laser_output_ON import execute_laser_on_measurement
from stools.s2Qualification.measurement_scripts.mode_AB_pulsing import execute_AB_measurement
from stools.s2Qualification.measurement_scripts.mode_A_pulsing import execute_mode_A_measurement
from stools.s2Qualification.measurement_scripts.mode_B_pulsing import execute_mode_B_measurement
from stools.s2Qualification.measurement_scripts.mode_C_pulsing import execute_mode_C_measurement
from stools.s2Qualification.measurement_scripts.mode_internal_pulsing import execute_internal_measurement
from stools.s2Qualification.measurement_scripts.with_wfg_measurement import execute_wfg_measurement
from stools.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from stools.utils.get_functions import get_s2_name, get_s2_type

ssrv_url = gConfig2.get_url('ssrv_restless')

if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()
    s2_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-000')
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')
    ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238')
    ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')
    wg_th = dms.get_instrument('HP/S2/INSTRUMENTS/AGILENT-WG')

    with dms.acquire_instruments(s2_th, oscillo_th, ps_th, ju_th, wg_th):
        oscillo = Oscilloscope(oscillo_th)
        power_supply = PowerSupply(ps_th)
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

            # Configure Measurement Internal
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

            # Configure Measurement modeA
            s2config = dict(pulsing_mode='modeA', voltage=8, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=250e-6)
            data = execute_mode_A_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeB
            s2config = dict(pulsing_mode='modeB', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=200e-6)
            data = execute_mode_B_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeCSS
            s2config = dict(pulsing_mode='modeCSS', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=2e-3)
            data = execute_mode_C_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement modeCST
            s2config = dict(pulsing_mode='modeCST', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=2.5e-3)
            data = execute_mode_C_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement laser on
            s2config = dict(pulsing_mode='modeCST', voltage=6, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=3, time_scale=2.5e-3)
            data = execute_laser_on_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)

            # Configure Measurement Internal overcurrent
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=400, current_limit=1)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            data["test_scope"]= 'OvCur_'
            save_measurement(get_s2_name(s2), data)
            power_supply.turn_off()
            power_supply.turn_on()
            power_supply.set_voltage(24.00)


            # Configure Power Supply 9 to 25V
            s2config = dict(pulsing_mode='internal', voltage=8, pulse_period=1000, pulse_width=400,
                            current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=4, offset_chan=0, chan_trig=2, time_scale=0.2e-6)
            for PowerSupplyVoltage in range(9, 26, 1):
                power_supply.set_voltage(PowerSupplyVoltage)
                data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
                data["test_scope"] = 'supply_{:.1f}V_'.format(PowerSupplyVoltage)
                save_measurement(get_s2_name(s2), data)
            power_supply.set_voltage(24.00)

            # Configure Measurement modeAB

            s2config = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=1000, current_limit=20,
                            voltage_A=8, voltage_B=5)
            s2.set_settings(**s2config)

            oscillo.set_settings(channel=1, volt_scale_chan=3, offset_chan=0, chan_trig=1, time_scale=5e-6)
            jura.set_relays({'IN_ARM': 'OFF',
                            'IN_SAFETY': 'OFF',
                            'MCU_OUT_INT': 'OFF',
                            'INTERLOCK': 'OFF',
                            'IN_MOD_DIR': 'ON',
                            'GND': 'ON'})
            wfg_frequencies = [16, 16, 16, 1000, 1000, 4000, 4000, 16]
            wfg_dutys = [0.01, 10, 16, 3, 80, 40, 96, 81]
            iiii = 0
            for freq, duty in zip(wfg_frequencies, wfg_dutys):
                oscillo.time_scale = 0.2 / freq
                wfg.set_settings(freq, duty, 1)
                wfg.enable_wfg()
                wg_info = '{}Hz_{}%'.format(freq, duty)
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


            # =========================== INTERLOCKS ===================================================================
            # IN ARM ON
            jura.set_relays({'IN_ARM': 'ON',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'ON'})
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=1, volt_scale_chan=4, offset_chan=0, chan_trig=1, time_scale=2e-3)

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
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=1000, current_limit=20)
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
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=1000, current_limit=20)
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
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=0.05)
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
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=50e-9)
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
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=1000, pulse_width=400, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=50e-9)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            data['test_scope'] = 'IN_ARM_SAFETY_'
            save_measurement(get_s2_name(s2), data)

        finally:
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            jura.switch_all_off()
            print('Execution time is: {:.1f} min'.format((time.time() - st)/60))