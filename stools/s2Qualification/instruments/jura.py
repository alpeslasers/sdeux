import time
from collections import OrderedDict

from dms import DMSManager


class Jura:

    def get_relays(self):
        return self.relays

    def __init__(self, th):
        self.th = th
        self.relays = OrderedDict({'IN_ARM': 'OFF',
                       'IN_SAFETY': 'OFF',
                       'MCU_OUT_INT': 'OFF',
                       'INTERLOCK': 'OFF',
                       'IN_MOD_DIR': 'OFF',
                       'GND': 'OFF'})

    def configure_relay(self, configuration):
        # The Arduino buffer is susceptible to concatenate messages if high velocity or small message sent ->
        # close the socket after each communication and wait some time.
        # self.th.write(configuration)
        self.th.query(configuration)
        time.sleep(1)

    def set_relays(self, relays):
        self.relays = relays
        self.set_up()

    def set_up(self):
        for relay, state in self.relays.items():
            self.configure_relay(relay + '_' + state)

    def switch_all_on(self):
        for relay in self.relays.keys():
            self.switch_on(relay)

    def switch_all_off(self):
        for relay in self.relays.keys():
            self.switch_off(relay)


    def get_state(self, relay):
        self.th.read(relay)

    def switch_on(self, relay):
        self.configure_relay(relay + '_ON')

    def switch_off(self, relay):
        self.configure_relay(relay + '_OFF')


if __name__ == '__main__':

    dms = DMSManager()
    jura_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238_local')
    with dms.acquire_instruments(jura_th):
        jura = Jura(jura_th)
        try:
            jura.set_relays({'IN_ARM': 'OFF',
                             'IN_SAFETY': 'OFF',
                             'MCU_OUT_INT': 'OFF',
                             'INTERLOCK': 'OFF',
                             'IN_MOD_DIR': 'OFF',
                             'GND': 'OFF'})
            time.sleep(1)
            jura.switch_on('IN_ARM')
            print('Switched on IN_ARM interlock')
            time.sleep(1)
            jura.switch_off('IN_ARM')
            print('Switched off IN_ARM interlock')
            time.sleep(1)

            jura.switch_on('IN_SAFETY')
            print('Switched on IN_SAFETY interlock')
            time.sleep(1)
            jura.switch_off('IN_SAFETY')
            print('Switched off IN_SAFETY interlock')
            time.sleep(1)

            jura.switch_on('MCU_OUT_INT')
            print('Switched on MCU_OUT_INT interlock')
            time.sleep(1)
            jura.switch_off('MCU_OUT_INT')
            print('Switched off MCU_OUT_INT interlock')
            time.sleep(1)

            jura.switch_on('INTERLOCK')
            print('Switched on INTERLOCK interlock')
            time.sleep(1)
            jura.switch_off('INTERLOCK')
            print('Switched off INTERLOCK interlock')
            time.sleep(1)

            jura.switch_on('IN_MOD_DIR')
            print('Switched on IN_MOD_DIR interlock')
            time.sleep(1)
            jura.switch_off('IN_MOD_DIR')
            print('Switched off IN_MOD_DIR interlock')
            time.sleep(1)

            jura.switch_on('GND')
            print('Switched on GND interlock')
            time.sleep(1)
            jura.switch_off('GND')
            print('Switched off GND interlock')
            time.sleep(1)


        finally:
            jura.switch_all_off()

