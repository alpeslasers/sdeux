import json
import time
from copy import copy
from time import sleep, strftime

from dms import DMSManager
from configuration_manager import gConfig2

from stools.auto_detect import init_driver
from stools.serial_handler import S2SerialHandler


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


