import time
from configuration_manager import gConfig2
import logging
from sdeux.auto_detect import init_driver
from sdeux.serial_handler import S2SerialHandler

ssrv_url = gConfig2.get_url('ssrv_restless')
logger = logging.getLogger(__name__)


if __name__ == '__main__':
    st = time.time()
    s2_th = S2SerialHandler('/dev/ttyUSB0')
    s2_th.open()
    s2 = None
    try:
        s2 = init_driver(s2_th)
        s2.set_up()
        s2.reset_overcurrent_flag()
        conf = dict(device_id=83, laser_id=b'', lasing_min_current=0.1, internal_limit=20,
                    modea_limit=20, modeb_limit=20, modecst_limit=20, modecss_limit=20,
                    modeab_a_limit=20, modeab_b_limit=20)
        s2.set_configuration(**conf)
        print(s2.configuration)
        s2.reload_info()
        if not s2.status_label == 'ok':
            raise Exception('S2 is not OK: {}'.format(s2.status_label))
 
    finally:
        s2.set_settings(pulsing_mode='off')
        s2_th.close()