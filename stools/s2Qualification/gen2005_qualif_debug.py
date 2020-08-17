import json
import time
from time import sleep
from configuration_manager import gConfig2
import logging
from stools.auto_detect import init_driver
from stools.serial_handler import S2SerialHandler

ssrv_url = gConfig2.get_url('ssrv_restless')
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    st = time.time()
    s2_th = S2SerialHandler('/dev/ttyUSB0') #s2
    s2_th.open()
    s2 = None
    try:
        s2 = init_driver(s2_th)
        s2.set_up()
        s2.reset_overcurrent_flag()
        s2.reload_info()
        if not s2.status_label == 'ok':
            raise Exception('S2 is not OK: {}'.format(s2.status_label))

        print(s2.info)

 
    finally:
        s2.set_settings(pulsing_mode='off')
        s2_th.close()