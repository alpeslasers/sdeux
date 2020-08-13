import json
import time
from copy import copy
from time import sleep

from dms import DMSManager
from configuration_manager import gConfig2
import logging


from pirata.drivers.S2.auto_detect import init_driver
# pip install --upgrade pirata command line to update pirata
from pirata.drivers.S2.defs import S2_STATUS_OK
from pirata.drivers.S2.serial_handler import S2SerialHandler

from elbit_scripts.s2Qualification.instruments.jura import Jura
from elbit_scripts.s2Qualification.instruments.oscilloscope import Oscilloscope
from elbit_scripts.s2Qualification.instruments.power_supply import PowerSupply
from elbit_scripts.s2Qualification.instruments.multimeter import MultiMeter
from elbit_scripts.s2Qualification.instruments.waveformgenerator import WaveFormGenerator
from elbit_scripts.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from elbit_scripts.utils.get_functions import get_s2_name, get_s2_type, get_pulser_info

ssrv_url = gConfig2.get_url('ssrv_restless')
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    st = time.time()
    s2_th = S2SerialHandler('/dev/ttyUSB0') #s2
    s2_th.open()
    s2 = None
    try:
        # Initialize s2 and check if sample in DB
        s2 = init_driver(s2_th)
        s2.set_up()
        time.sleep(2)
        # s2config = dict(pulsing_mode='modeAB', pulse_period=1000, pulse_width=None, current_limit=20,
        #                 voltage_A=5, voltage_B=2, pulse_width_A=300, pulse_width_B=500, current_limit_mode=0)
        # s2.set_settings(**s2config)
        debug= s2.query_debug_info()
        print(debug)
        i= json.dumps("{}".format(debug))
        print(i)
 
    finally:
        # s2.set_settings(pulsing_mode='off')
        s2_th.close()