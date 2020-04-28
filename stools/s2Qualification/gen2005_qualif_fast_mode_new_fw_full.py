import json
import struct
import time
from copy import copy
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import cumtrapz as tpz

from dms import DMSManager
from configuration_manager import gConfig2

from stools.auto_detect import init_driver
from stools.serial_handler import S2SerialHandler
from stools.s2Qualification.instruments.jura import Jura
from stools.s2Qualification.instruments.oscilloscope import Oscilloscope
from stools.s2Qualification.instruments.power_supply import PowerSupply
from stools.s2Qualification.instruments.multimeter import MultiMeter

ssrv_url = gConfig2.get_url('ssrv_restless')


PRESET_1 = 3
PRESET_2 = 22

if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()
    s2_th = S2SerialHandler('/dev/tty.usbserial-FTV8G4AG') #s2
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')  #oscilloscope
    ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238_local')  #JURA
    ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')  #p ower supply
    mm_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200252')  # multimetrer K2000

    with dms.acquire_instruments(oscillo_th, ps_th, ju_th, mm_th):
        oscillo = Oscilloscope(oscillo_th)
        oscillo.set_single_acquisition_mode()
        power_supply = PowerSupply(ps_th)
        mm = MultiMeter(mm_th)
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

            print('Opening serial, configuring fast mode')

            s2_th.open()
            # Initialize s2 and check if sample in DB
            s2 = init_driver(s2_th)
            s2.set_up()
            # Packet transmission speed: osc channel 1 should be connected to the tx line at the output of the Chipix.
            s2.configure_fast_mode_presets(preset_number=PRESET_1, pulse_period=1000, pulse_width=10)
            s2.configure_fast_mode_presets(preset_number=PRESET_2, pulse_period=10000, pulse_width=1000)
            s2set = dict(pulsing_mode='internal_fast', voltage=5.0, current_limit=0.2)
            s2.set_settings(**s2set)
            s2_th.close()
            time.sleep(0.1)


            print('Preset 1')
            s2_th.open()
            s2_th.write(bytes([PRESET_1]))
            time.sleep(0.5)


            print('Preset 2')
            s2_th.write(bytes([PRESET_2]))
            # The time scale should be adjusted manually
            oscillo.set_settings_fast(channel=1, volt_scale_chan=2, offset_chan=0, time_scale=200e-3)
            time.sleep(5)

            x_ref, data_ref = oscillo.drive_fast()
            oscillo.channel=2

            x_s2, data_s2 = oscillo.drive_fast()

        finally:
            s2.set_settings(pulsing_mode='off')
            s2_th.close()
            power_supply.turn_off()
            power_supply.release()
            jura.switch_all_off()
            time_test_min = int((time.time() - st) / 60)
            time_test_sec = int((time.time() - st) % 60)
            print('Execution time is: {} min {} sec'.format(time_test_min, time_test_sec))

            # serial pulse
            fig = plt.figure()
            ax = fig.add_subplot(111)  # The big subplot
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            ax.set_xlabel("time(s)")
            ax1.set_ylabel("RS232 Tx line")
            ax1.plot(x_ref, data_ref)
            ax2.set_ylabel("S2 Output")
            ax2.plot(x_s2, data_s2)
            plt.show()

