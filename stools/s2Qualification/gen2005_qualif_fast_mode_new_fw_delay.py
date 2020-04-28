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

from pirata.drivers.S2.auto_detect import init_driver
# pip install --upgrade pirata command line to update pirata
from pirata.drivers.S2.serial_handler import S2SerialHandler
from elbit_scripts.s2Qualification.instruments.jura import Jura
from elbit_scripts.s2Qualification.instruments.oscilloscope import Oscilloscope
from elbit_scripts.s2Qualification.instruments.power_supply import PowerSupply
from elbit_scripts.s2Qualification.instruments.multimeter import MultiMeter
from elbit_scripts.s2Qualification.ssrv_communication import save_measurement
from elbit_scripts.utils.get_functions import get_s2_name, get_pulser_info

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
            laser_id = s2.info.laser_id
            pulser_info = get_pulser_info(s2)
            pulser_info['laser_id'] = '{}'.format(laser_id)
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
            oscillo.set_settings_fast(channel=1, volt_scale_chan=2, offset_chan=0, time_scale=1e-3)
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

            # Detecting data pulse
            x_ref_clip = np.array(x_ref[0:])
            data_ref_clip = data_ref[0:]
            # Detecting steps by convolving two opposite signals to give a max
            data_ref_clip -= np.average(data_ref_clip)
            # If mean should decrease, the hstack should be opposite sign (if mean at the start is > mean at the end)
            step = np.hstack((np.ones(len(data_ref_clip)), -1 * np.ones(len(data_ref_clip))))
            dary_step = np.convolve(data_ref_clip, step, mode='valid')
            # get the peak of the convolution, its index
            step_indx = np.argmax(dary_step)
            ind = step_indx
            data_pulse_time = x_ref[ind]

            # Detecting signal change (pulse widths)
            x_s2_clip = np.array(x_s2[0:])
            data_s2_clip = data_s2[0:]
            N = 2
            mean1 = [np.mean(data_s2_clip[x:x + N]) for x in range(len(data_s2_clip) - N + 1)]
            x = np.linspace(x_s2[0], x_s2[-1], len(mean1), endpoint=False)
            y = tpz(data_s2_clip, x=x_s2_clip)
            # Detecting steps by convolving two opposite signals to give a max
            mean1 -= np.average(mean1)
            # If mean should decrease, the hstack should be opposite sign (if mean at the start is > mean at the end)
            step1 = np.hstack((np.ones(len(mean1)), -1 * np.ones(len(mean1))))
            dary_step1 = np.convolve(mean1, step1, mode='valid')
            # get the peak of the convolution, its index
            step_indx = np.argmax(dary_step1)
            index = step_indx
            pulse_time = x_s2[index]
            delay = pulse_time - data_pulse_time
            print('Measured delay (s): {}'.format(delay))
            # Save data
            measurement_data = {'test_scope': 'fast_presets',
                                'rs232_time_ref': x_ref,
                                's2_output_time_ref': x_s2,
                                'rs232_signal_volt': data_ref,
                                's2_output_sign_volt': data_s2,
                                'rs232_edge_time': pulse_time,
                                'S2_pulse_change_time': data_pulse_time,
                                'response delay': delay,
                                "pulser_info": json.dumps(pulser_info),
                                }
            save_measurement(get_s2_name(s2), measurement_data, measure_type="s2_fast_mode")

            # Plot
            # serial pulse
            fig = plt.figure()
            ax = fig.add_subplot(111)  # The big subplot
            ax1 = fig.add_subplot(211)
            ax2 = fig.add_subplot(212)
            ax.set_xlabel("time(s)")
            ax1.set_ylabel("RS232 Tx line")
            ax1.plot(x_ref, data_ref)
            ax1.axvline(data_pulse_time, color='r')
            ax2.set_ylabel("S2 Output")
            ax2.plot(x_s2, data_s2)
            ax2.plot(x, mean1)
            ax2.axvline(pulse_time, color='r')
            plt.show()

