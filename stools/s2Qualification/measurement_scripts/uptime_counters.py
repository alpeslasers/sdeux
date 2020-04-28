import json
from dms import DMSManager
from configuration_manager import gConfig2

from pirata.drivers.S2.auto_detect import init_driver

from elbit_scripts.s2Qualification.instruments.jura import Jura
from elbit_scripts.s2Qualification.instruments.oscilloscope import Oscilloscope
from elbit_scripts.s2Qualification.instruments.power_supply import PowerSupply
from elbit_scripts.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from elbit_scripts.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')


def execute_time_counters_measurement(s2, s2config, powersupply, jura, intial_uptime, final_uptime, start_time, end_time):
    s2.reload_info()
    pulser_info = get_pulser_info(s2)
    measurement_data = {"applied_voltage": s2.info.input_voltage_measured,
                        "power_supply_voltage": powersupply.get_voltage(),
                        "test_scope": 'Tim_',
                        "current": s2.info.output_current_measured,
                        "voltage": s2.info.output_voltage_measured,
                        "pulser_info": json.dumps(pulser_info),
                        "pulse_mode": s2config["pulsing_mode"],
                        "duty_cycle": round(s2config['pulse_width'] / s2config['pulse_period'], 2),
                        "pulse_length": s2config['pulse_width'],
                        "s2_meas_lasing": final_uptime.lasing_time - intial_uptime.lasing_time,
                        "lasing": end_time - start_time if s2.info.output_current_measured >= 0.1 else 0,
                        "s2_meas_operation": final_uptime.operation_time - intial_uptime.operation_time,
                        "operation": end_time - start_time if s2.info.output_voltage_measured >= 5 else 0,
                        "s2_meas_uptime": final_uptime.uptime - intial_uptime.uptime,
                        "uptime": end_time - start_time,
                        "relays_info": jura.get_relays(),
                        }
    return measurement_data