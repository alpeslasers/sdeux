class WaveFormGenerator:

    @property
    def frequency(self):
        return self._frequency

    @property
    def duty(self):
        return self._duty

    @property
    def output(self):
        return self._output

    @frequency.setter
    def frequency(self, val):
        self._frequency = val

    @duty.setter
    def duty(self, val):
        self._duty = val

    @output.setter
    def output(self, val):
        self._output = val

    def __init__(self, th):
        self.th = th
        self._frequency = None
        self._duty = None
        self._output = None

    def set_settings(self, frequency, duty, output):
        self._frequency = frequency
        self._duty = duty
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

    def disable(self):
        self._write(':OUTP 0')
