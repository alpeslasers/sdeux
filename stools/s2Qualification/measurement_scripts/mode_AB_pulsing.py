import json

import time
from dms import DMSManager
from configuration_manager import gConfig2

from pirata.drivers.S2.auto_detect import init_driver

from elbit_scripts.s2Qualification.instruments.jura import Jura
from elbit_scripts.s2Qualification.instruments.oscilloscope import Oscilloscope
from elbit_scripts.s2Qualification.instruments.power_supply import PowerSupply
from elbit_scripts.s2Qualification.instruments.waveformgenerator import WaveFormGenerator
from elbit_scripts.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from elbit_scripts.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')


def execute_AB_measurement(s2, s2config, oscillo, powersupply, jura):
    s2.reload_info()
    pulser_info = get_pulser_info(s2)
    oscillo.set_trig_edge_source()
    oscillo.set_trig_level()
    amplitude_ref, pos_duty_ref, puls_width_ref, period_ref, x_ref, data_ref, vmax_chan4 = oscillo.drive()
    oscillo.channel = 2
    oscillo.set_trig_edge_source()
    oscillo.set_trig_level()
    amplitude_s2, pos_duty_s2, puls_width_s2, period_s2, x_s2, data_s2, vmax_chan4 = oscillo.drive()

    measurement_data = {"applied_voltage": s2.info.input_voltage_measured,
                        "power_supply_voltage": powersupply.get_voltage(),
                        "test_scope": '',
                        "current": s2.info.output_current_measured,
                        "voltage": s2.info.output_voltage_measured,
                        "pulser_info": json.dumps(pulser_info),
                        "pulse_mode": s2config["pulsing_mode"],
                        #"duty_cycle": round(s2config['pulse_width'] / s2config['pulse_period'], 2),
                        "pulse_length": s2config['pulse_width'],
                        "s2_wf_amplitude": amplitude_s2,
                        "s2_wf_duty": pos_duty_s2,
                        "s2_wf_negative_width": puls_width_s2,
                        "s2_wf_period": period_s2,
                        "s2_wf_trac_t": x_s2,
                        "s2_wf_trac_v": data_s2,
                        "relays_info": jura.get_relays(),
                        "ref_wf_amplitude": amplitude_ref,
                        "ref_wf_duty":pos_duty_ref,
                        "ref_wf_negative_width": puls_width_ref,
                        "ref_wf_period": period_ref,
                        "ref_wf_trac_t": x_ref,
                        "ref_wf_trac_v": data_ref,
                        "mcu_out": vmax_chan4
                        }
    return measurement_data

if __name__ == '__main__':

    dms = DMSManager()
    s2_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-000')
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')
    ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238_local')
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
                             'IN_MOD_DIR': 'ON',
                             'GND': 'ON'})
            power_supply.set_up()
            power_supply.set_voltage(24.00)

            # Initialize s2 and check if sample in DB
            s2 = init_driver(s2_th)
            s2.set_up()
            check_sample_in_db(get_s2_name(s2), get_s2_type(s2))

            # Configure Measurement
            s2config = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=1000, current_limit=20,
                            voltage_A=8, voltage_B=5)
            s2.set_settings(**s2config)

            oscillo.set_settings(channel=1, volt_scale_chan=2, offset_chan=0, chan_trig=1, time_scale=5e-6)

            wfg_frequencies = [16, 16, 16, 1000, 1000, 4000, 4000, 16]
            wfg_dutys = [0.01, 10, 16, 3, 80, 40, 96, 81]
            for freq, duty in zip(wfg_frequencies, wfg_dutys):
                oscillo.time_scale = 0.2 / freq
                wfg.set_settings(freq, duty, 1)
                wfg.enable_wfg()
                wg_info = '{}Hz_{}%'.format(freq, duty)
                data = execute_AB_measurement(s2, s2config, oscillo, power_supply, jura)
                data['test_scope'] = wg_info
                save_measurement(get_s2_name(s2), data)

        finally:
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            jura.switch_all_off()