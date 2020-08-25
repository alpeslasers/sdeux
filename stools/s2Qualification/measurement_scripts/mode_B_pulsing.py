from dms import DMSManager
from configuration_manager import gConfig2

from stools.auto_detect import init_driver

from stools.s2Qualification.instruments.jura import Jura
from stools.s2Qualification.measurement_scripts.mode_internal_pulsing import execute_internal_measurement
from stools.s2Qualification.instruments.oscilloscope import Oscilloscope
from stools.s2Qualification.instruments.power_supply import PowerSupply
from stools.s2Qualification.ssrv_communication import check_sample_in_db, save_measurement
from stools.utils.get_functions import get_s2_name, get_s2_type

ssrv_url = gConfig2.get_url('ssrv_restless')


def execute_mode_B_measurement(s2, s2config, oscillo, powersupply, jura):
    return execute_internal_measurement(s2, s2config, oscillo, powersupply, jura)


if __name__ == '__main__':

    dms = DMSManager()
    s2_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-000')
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')
    ju_th = dms.get_instrument('HP/S2/INSTRUMENTS/ARDUINO_UNO_200238_local')
    ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')

    with dms.acquire_instruments(s2_th, oscillo_th, ps_th, ju_th):
        oscillo = Oscilloscope(oscillo_th)
        power_supply = PowerSupply(ps_th)
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

            # Initialize s2 and check if sample in DB
            s2 = init_driver(s2_th)
            s2.set_up()
            check_sample_in_db(get_s2_name(s2), get_s2_type(s2))

            # Configure Measurement
            s2config = dict(pulsing_mode='modeB', voltage=6, pulse_period=2000, pulse_width=1000, current_limit=20)
            s2.set_settings(**s2config)
            oscillo.set_settings(channel=2, volt_scale_chan=3, offset_chan=0, chan_trig=2, time_scale=200e-6)
            data = execute_mode_B_measurement(s2, s2config, oscillo, power_supply, jura)
            save_measurement(get_s2_name(s2), data)
        finally:
            s2.set_settings(pulsing_mode='off')
            power_supply.turn_off()
            jura.switch_all_off()
