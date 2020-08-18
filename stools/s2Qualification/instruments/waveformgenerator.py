from dms import DMSManager


class WaveFormGenerator:

    @property
    def frequency(self):
        return self._frequency

    @property
    def duty(self):
        return self._duty

    @property
    def burst_period(self):
        return self._burst_period

    @property
    def output(self):
        return self._output

    @frequency.setter
    def frequency(self, val):
        self._frequency = val

    @duty.setter
    def duty(self, val):
        self._duty = val

    @burst_period.setter
    def burst_period(self, val):
        self._burst_period = val

    @output.setter
    def output(self, val):
        self._output = val

    def __init__(self, th):
        self.th = th
        self._frequency = None
        self._duty = None
        self._output = None
        self._burst_period = None

    def set_settings(self, frequency, duty, output):
        self._frequency = frequency
        self._duty = duty
        self._output = output

    def set_settings_burst(self, duty, frequency, burst_period, output):
        self._duty = duty
        self._frequency = frequency
        self._burst_period = burst_period
        self._output = output

    def _write(self, cmd):
        self.th.write(cmd)

    def enable_wfg(self):
        self._write(':FUNC SQU')
        self._write(':FUNC:SQU:DCYC {}'.format(self.duty))
        self._write(':FREQ {}'.format(self.frequency))
        self._write(':VOLT:HIGH +3.3')
        self._write(':VOLT:LOW +0')
        self._write(':OUTP1:LOAD INF')
        self._write(':OUTP {}'.format(self.output))

    def enable_burst(self):
        self._write(':FUNC SQU')
        self._write(':FUNC:SQU:DCYC {}'.format(self.duty))
        self._write(':FREQ {}'.format(self.frequency))
        self._write(':BURS:MODE TRIG')
        self._write(':BURS:NCYC 3')
        self._write(':BURS:INT:PER {}'.format(self.burst_period))
        self._write(':TRIG:SOUR IMM')
        self._write(':BURS:STAT ON')
        self._write(':VOLT:HIGH +3.3')
        self._write(':VOLT:LOW +0')
        self._write(':OUTP1:LOAD INF')
        self._write(':OUTP {}'.format(self.output))


    def inject_modeB_input(self):
        self._write(':FUNC SQU')
        self._write(':TRIG:SOUR IMM')
        self._write(':FREQ:MODE LIST')
        self._write(':LIST:DWELl +9.0E-04')
        self._write(':LIST:FREQ +1.64E+03,+3.33E+04,+1.64E+03')
        self._write(':VOLT:HIGH +3.3')
        self._write(':VOLT:LOW +0')
        self._write(':OUTP 1')

    def disable(self):
        self._write(':OUTP 0')


if __name__ == '__main__':
    dms = DMSManager()
    wg_th = dms.get_instrument('HP/S2/INSTRUMENTS/AGILENT-WG')  # waveform generator
    with dms.acquire_instruments(wg_th):
        wfg = WaveFormGenerator(wg_th)
        try:
            wfg.inject_modeB_input()
        finally:
            wfg.disable()


