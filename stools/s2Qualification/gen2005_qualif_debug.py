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

        device_id = s2.info.device_id
        laser_id = s2.info.laser_id
        sleep(2)
        conf = dict(device_id=device_id, laser_id=laser_id, mode_auto_duty_limit_low=0.13, mode_auto_duty_limit_high=0.11, mode_auto_high_secur_delay= 1000000,
                               lasing_min_current=0, internal_limit=20, modea_limit=20, modeb_limit=20, modecst_limit=20,
                               modecss_limit=20, mode_auto_high_limit=20, mode_auto_low_limit=20, integr_t_auto=450000)
        print(s2.set_configuration(**conf))
        sleep(1)
        s2config = dict(pulsing_mode='modeAUTO', pulse_period=1000, pulse_width=None, current_limit=20,
                        output_voltage_set_auto_high=5, output_voltage_set_auto_low=2, pulse_width_auto_high=300, pulse_width_auto_low=500, current_limit_mode=0)
        s2.set_settings(**s2config)
        sleep(2)
        debug= s2.query_debug_info()
        print(debug)
 
    finally:
        s2.set_settings(pulsing_mode='off')
        s2_th.close()