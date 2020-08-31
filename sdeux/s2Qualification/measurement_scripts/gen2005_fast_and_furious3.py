import json
import time
from copy import copy
from time import sleep, strftime

from dms import DMSManager
from configuration_manager import gConfig2

from sdeux.communication import create_packet
from sdeux.defs import S2_PACKET_SET_SETTINGS, S2_PULSING_INTERNAL
from sdeux.gen2005 import S2, S2Settings
from sdeux.serial_handler import S2SerialHandler

ssrv_url = gConfig2.get_url('ssrv_restless')

if __name__ == '__main__':
    st = time.time()
    dms = DMSManager()

    s2_th = S2SerialHandler('/dev/tty.usbserial-FTV8G4AG')
    s2_th.open()

    s2 = S2(th=s2_th)

    s2_settings = S2Settings.default()
    s2_settings.pulsing_mode = S2_PULSING_INTERNAL
    s2_settings.output_voltage_set = 4
    s2_settings.pulse_period = 10000
    s2_settings.pulse_width = 900
    s2_settings.output_current_limit = 20
    packet = create_packet(S2_PACKET_SET_SETTINGS, s2_settings)
    s2._query_packet(packet, s2_settings)



