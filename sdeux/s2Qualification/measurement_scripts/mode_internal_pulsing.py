import json
from time import sleep

from dms import DMSManager
from configuration_manager import gConfig2

from sdeux.auto_detect import init_driver

from sdeux.s2Qualification.instruments.jura import Jura
from sdeux.s2Qualification.instruments.oscilloscope import Oscilloscope
from sdeux.s2Qualification.instruments.power_supply import PowerSupply
from sdeux.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from sdeux.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')


def execute_internal_measurement(s2, s2config, oscillo, powersupply, jura):
    s2.reload_info()
    pulser_info = get_pulser_info(s2)
    sleep(1)
    oscillo.set_trig_edge_source()
    oscillo.set_trig_level()
    amplitude, pos_duty, puls_width, period, x, data, vmax_chan4 = oscillo.drive()
    measurement_data = {"applied_voltage": s2.info.input_voltage_measured,
                        "power_supply_voltage": powersupply.get_voltage(),
                        "test_scope": '',
                        "current": s2.info.output_current_measured,
                        "voltage": s2.info.output_voltage_measured,
                        "pulser_info": json.dumps(pulser_info),
                        "pulse_mode": s2config["pulsing_mode"],
                        "duty_cycle": round(float(s2config['pulse_width']) / float(s2config['pulse_period']), 2),
                        "pulse_length": s2config['pulse_width'],
                        "s2_wf_amplitude": amplitude,
                        "s2_wf_duty": pos_duty,
                        "s2_wf_negative_width": puls_width,
                        "s2_wf_period": period,
                        "s2_wf_trac_t": x,
                        "s2_wf_trac_v": data,
                        "relays_info": jura.get_relays(),
                        "mcu_out": vmax_chan4
                        }
    return measurement_data


if __name__ == '__main__':

    dms = DMSManager()
    s2_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-000')
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')
    ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238_local')
    ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')

    with dms.acquire_instruments(s2_th, oscillo_th, ps_th, ju_th):
        oscillo = Oscilloscope(oscillo_th)
        power_supply = PowerSupply(ps_th)
        jura = Jura(ju_th)
        s2 = None
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

            # Configure Measurement
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=15000, pulse_width=300, current_limit=20)
            s2.set_settings(**s2config)
            print(get_pulser_info(s2))

            oscillo.set_settings(channel=2, volt_scale_chan=5, offset_chan=0, chan_trig=2, time_scale=3e-6)
            data = execute_internal_measurement(s2, s2config, oscillo, power_supply, jura)
            #save_measurement(get_s2_name(s2), data)

        finally:
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            jura.switch_all_off()