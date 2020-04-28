import json
import time
from copy import copy
from time import sleep, strftime

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

if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()
    # s2_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-000')
    s2_th = S2SerialHandler('/dev/tty.usbserial-FTV8G4AG')
    s2_th.open()
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')  #oscilloscope
    # ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238')  #JURA
    # ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')  #p ower supply
    # wg_th = dms.get_instrument('HP/S2/INSTRUMENTS/AGILENT-WG')  #waveform generator
    # mm_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200252')  # multimètre K2000

    with dms.acquire_instruments(oscillo_th):
        # oscillo = Oscilloscope(oscillo_th)
        # power_supply = PowerSupply(ps_th)
        # mm = MultiMeter(mm_th)
        # jura = Jura(ju_th)
        s2 = None
        # wfg = WaveFormGenerator(wg_th)
        try:
            # # Configure JURA and POWER SUPPLY
            # jura.set_relays({'IN_ARM': 'OFF',
            #                  'IN_SAFETY': 'OFF',
            #                  'MCU_OUT_INT': 'OFF',
            #                  'INTERLOCK': 'OFF',
            #                  'IN_MOD_DIR': 'OFF',
            #                  'GND': 'OFF'})
            # power_supply.set_up()
            # power_supply.set_voltage(24.00)

            # Initialize s2 and check if sample in DB
            s2 = init_driver(s2_th)
            s2.set_up()
            check_sample_in_db(get_s2_name(s2), get_s2_type(s2))



            # Configure Measurement Internal
            s2config = dict(pulsing_mode='internal', voltage=10, pulse_period=10000, pulse_width=5000, current_limit=20)
            s2.set_settings(**s2config)
            sleep(1)

        finally:
            s2.set_settings(pulsing_mode='off')
            # power_supply.output_off()
            # power_supply.release()
            # jura.switch_all_off()
            s2_th.close()
            time_test_min = int((time.time() - st) / 60)
            time_test_sec = int((time.time() - st) % 60)
            print('Execution time is: {} min {} sec'.format(time_test_min, time_test_sec))

