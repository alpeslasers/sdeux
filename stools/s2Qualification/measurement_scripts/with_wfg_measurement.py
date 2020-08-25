import json
from time import sleep

from stools.utils.get_functions import get_pulser_info


def execute_wfg_measurement(s2, s2config, oscillo, powersupply, jura, second_channel):
    s2.reload_info()
    pulser_info = get_pulser_info(s2)
    oscillo.set_trig_edge_source()
    oscillo.set_trig_level()
    amplitude_ref, pos_duty_ref, puls_width_ref, period_ref, x_ref, data_ref, vmax_chan4 = oscillo.drive()
    oscillo.channel = second_channel
    amplitude_s2, pos_duty_s2, puls_width_s2, period_s2, x_s2, data_s2, vmax_chan4 = oscillo.drive()

    measurement_data = {"applied_voltage": s2.info.input_voltage_measured,
                        "power_supply_voltage": powersupply.get_voltage(),
                        "test_scope": '',
                        "current": s2.info.output_current_measured,
                        "voltage": s2.info.output_voltage_measured,
                        "pulser_info": json.dumps(pulser_info),
                        "pulse_mode": s2config["pulsing_mode"],
                        "duty_cycle": round(float(s2config['pulse_width']) / float(s2config['pulse_period']), 2),
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
