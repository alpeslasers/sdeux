import json
import time
from copy import copy
from time import sleep, strftime

from dms import DMSManager
from configuration_manager import gConfig2

from pirata.drivers.S2.auto_detect import init_driver
from pirata.drivers.S2.serial_handler import S2SerialHandler

from elbit_scripts.s2Qualification.instruments.jura import Jura
from elbit_scripts.s2Qualification.instruments.oscilloscope import Oscilloscope
from elbit_scripts.s2Qualification.instruments.power_supply import PowerSupply
from elbit_scripts.s2Qualification.instruments.multimeter import MultiMeter
from elbit_scripts.s2Qualification.instruments.waveformgenerator import WaveFormGenerator
from elbit_scripts.s2Qualification.measurement_scripts.Laser_output_ON import execute_laser_on_measurement
from elbit_scripts.s2Qualification.measurement_scripts.mode_AB_pulsing import execute_AB_measurement
from elbit_scripts.s2Qualification.measurement_scripts.mode_A_pulsing import execute_mode_A_measurement
from elbit_scripts.s2Qualification.measurement_scripts.mode_B_pulsing import execute_mode_B_measurement
from elbit_scripts.s2Qualification.measurement_scripts.mode_C_pulsing import execute_mode_C_measurement
from elbit_scripts.s2Qualification.measurement_scripts.mode_internal_pulsing import execute_internal_measurement
from elbit_scripts.s2Qualification.measurement_scripts.uptime_counters import execute_time_counters_measurement
from elbit_scripts.s2Qualification.measurement_scripts.with_wfg_measurement import execute_wfg_measurement
from elbit_scripts.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from elbit_scripts.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')

if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()

    s2_th = S2SerialHandler('/dev/tty.usbserial-FTV8G4AG')
    s2_th.open()

    s2 = init_driver(s2_th)
    s2.set_up()
            # Configure Measurement Internal
    s2config = dict(pulsing_mode='internal', voltage=2, pulse_period=10000, pulse_width=5000, current_limit=20)
    s2.set_settings(**s2config)


