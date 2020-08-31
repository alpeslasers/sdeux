import time

from dms import DMSManager

class PowerSupply:

    def __init__(self, th):
        self.th = th

    def _write(self, cmd):
        self.th.write(cmd)
        time.sleep(0.5)

    def _query(self, cmd):
        res = self.th.query(cmd)
        time.sleep(0.5)
        return res

    def set_current(self, val):
        self._write("CURR " + str(val))

    def set_voltage(self, val):
        self._write("VOLT " + str(val))

    def set_up(self):
        self._write("SYST:REM")
        self._write("*RST")
        self._write("VOLT:RANG P30V")
        self.set_current(4.00)
        self.set_voltage(30.0)
        self.set_voltage(0.0)
        self.turn_on()

    def get_voltage(self):
        return float(self._query("MEAS:VOLT?"))

    def get_current(self):
        return float(self._query("MEAS:CURR?"))

    def turn_on(self):
        self._write("OUTP ON")

    def release(self):
        self._write("SYST:LOC")

    def turn_off(self):
        self.set_voltage(0.0)
        self._write("OUTP OFF")

    def output_off(self):
        self._write("OUTP OFF")


if __name__ == '__main__':

    dms = DMSManager()
    ps_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200237')
    with dms.acquire_instruments(ps_th):
        ps = PowerSupply(ps_th)
        try:
            ps.set_up()
            print("Measured voltage: {0}, Measured current: {1}".format(ps.get_voltage(), ps.get_current()))
            ps.set_voltage(3)
            print("Measured voltage: {0}, Measured current: {1}".format(ps.get_voltage(), ps.get_current()))
            ps.set_voltage(5)
            print("Measured voltage: {0}, Measured current: {1}".format(ps.get_voltage(), ps.get_current()))
        finally:
            ps.turn_off()
