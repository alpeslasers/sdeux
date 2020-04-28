import numpy as np
from dms import DMSManager
import time


class Oscilloscope:

    @property
    def channel(self):
        return self._channel

    @property
    def volt_scale_chan(self):
        return self._volt_scale_chan

    @property
    def offset_chan(self):
        return self._offset_chan

    @property
    def chan_trig(self):
        return self._chan_trig

    @property
    def time_scale(self):
        return self._time_scale

    @channel.setter
    def channel(self, val):
        self._channel = val

    @volt_scale_chan.setter
    def volt_scale_chan(self, val):
        self._volt_scale_chan = val

    @offset_chan.setter
    def offset_chan(self, val):
        self._offset_chan = val

    @chan_trig.setter
    def chan_trig(self, val):
        self._chan_trig = val

    @time_scale.setter
    def time_scale(self, val):
        self._time_scale = val

    def __init__(self, th):
            self.th = th
            self._channel = None
            self._volt_scale_chan = None
            self._offset_chan = None
            self._chan_trig = None
            self._time_scale = None

    def set_settings(self, channel, volt_scale_chan, offset_chan, chan_trig, time_scale):
        self._channel = channel
        self._volt_scale_chan = volt_scale_chan
        self._offset_chan = offset_chan
        self._chan_trig = chan_trig
        self._time_scale = time_scale

    # function used for fast mode validation
    def set_settings_fast(self, channel, volt_scale_chan, offset_chan, time_scale):
        self._channel = channel
        self._volt_scale_chan = volt_scale_chan
        self._offset_chan = offset_chan
        self._time_scale = time_scale

    def set_trig_edge_source(self):
        self.th.write(':TRIG:MODE EDGE')
        self.th.write(':TRIG:EDGE:SLOP POS') # set trigger at rising edge
        self.th.write(':TRIG:EDGE:SOUR CHAN{}'.format(self.chan_trig)) # selection de la source de trigger

    def cursor_position(self, delay_trigger):
        self.th.write(':TIM:POS {}'.format(delay_trigger))

    def set_trig_level(self):
        self.th.write(':TRIG:LEV 2')  # trigger level a 2V
        #self.th.write(':TRIG:LEV:ASET')  # trigger at 50%

    def set_trig_type_pulse_width(self, delay_trigger, pulse_width_min, pulse_width_max, channel, polarity):
        self.th.write(':TIM:POS {}'.format(delay_trigger))
        self.th.write(':TRIG:MODE GLIT')
        self.th.write(':TRIG:GLIT:RANG {}ns, {}ns'.format(pulse_width_min, pulse_width_max))
        self.th.write(':TRIG:GLIT:SOUR CHAN{}'.format(channel))
        self.th.write(':TRIG:GLIT:POL {}'.format(polarity))

    def get_delay(self, channel1, channel2):
        st = ':MEAS:DEL? CHAN{0},CHAN{1}'.format(channel1, channel2)
        self.th.write(st)
        rd = float(self.th.read())
        return rd

        # function used for fast mode validation
    def set_single_acquisition_mode(self):
        self.th.write(':SING')

    def drive(self):

        # Channel
        self.th.write(':CHAN{}:DISP 1'.format(self.channel))
        self.th.write(':CHAN{}:OFFS {}'.format(self.channel, self.offset_chan))  # offset by default in volt
        self.th.write(':CHAN{}:SCAL {}'.format(self.channel, self.volt_scale_chan))  # scale by default V/div

        # common parameters
        self.th.write(':TIMebase:SCAL {}'.format(self.time_scale))  # scale time[s]/div
        # waveform acquisition
        self.th.write(':CHAN2:INV 1')
        self.th.write(':CHAN1:INV 0')

        self.th.write(':WAV:SOUR CHAN{}'.format(self.channel))  # choose of the channel for acquisition
        self.th.write(':WAV:FORM ASC')  # format acsii
        dx = float(self.th.query(':WAV:XINC?'))  # step in axis x
        data = (self.th.query(':WAV:DATA?')).decode('utf-8')  # acqusition waveform without x axis
        header_len = int(data[1]) + 2
        data = data[header_len:]
        data = [float(x) for x in data.split(',')]
        data = np.array(data)[1:]
        x = [dx * float(p) for p in range(0, len(data), 1)]

        # measurements
        amplitude = float(self.th.query(':MEAS:VAMP? CHAN{}'.format(self.channel)).decode('utf-8'))
        pos_duty = float(self.th.query(':MEAS:DUTY? CHAN{}'.format(self.channel)).decode('utf-8'))
        puls_width = float(self.th.query(':MEAS:PWID? CHAN{}'.format(self.channel)).decode('utf-8'))
        period = float(self.th.query(':MEAS:PER? CHAN{}'.format(self.channel)).decode('utf-8'))
        vmax_chan4 = float(self.th.query(':MEAS:VRMS? DISP,DC,CHAN4').decode('utf-8'))

        return amplitude, pos_duty, puls_width, period, x, data.tolist(), vmax_chan4

    # function used for fast mode validation
    def drive_fast(self):

        # Channel
        self.th.write(':CHAN{}:DISP 1'.format(self.channel))
        self.th.write(':CHAN{}:OFFS {}'.format(self.channel, self.offset_chan))  # offset by default in volt
        self.th.write(':CHAN{}:SCAL {}'.format(self.channel, self.volt_scale_chan))  # scale by default V/div

        # common parameters
        self.th.write(':TIMebase:SCAL {}'.format(self.time_scale))  # scale time[s]/div
        # waveform acquisition
        self.th.write(':CHAN2:INV 1')
        self.th.write(':CHAN1:INV 0')

        self.th.write(':WAV:SOUR CHAN{}'.format(self.channel))  # choose of the channel for acquisition
        self.th.write(':WAV:FORM ASC')  # format acsii
        dx = float(self.th.query(':WAV:XINC?'))  # step in axis x
        data = (self.th.query(':WAV:DATA?')).decode('utf-8')  # acqusition waveform without x axis
        header_len = int(data[1]) + 2
        data = data[header_len:]
        data = [float(x) for x in data.split(',')]
        data = np.array(data)[1:]
        x = [dx * float(p) for p in range(0, len(data), 1)]

        return x, data.tolist()


if __name__ == '__main__':
    dms = DMSManager()
    oscillo_th = dms.get_instrument('HP/S2/INSTRUMENTS/DSOX')  # oscilloscope
    with dms.acquire_instruments(oscillo_th):
        oscillo = Oscilloscope(oscillo_th)
        try:
            oscillo.set_settings(channel=1, volt_scale_chan=2.5, offset_chan=1, chan_trig=1, time_scale=2e-6)
            oscillo.set_trig_edge_source()
            oscillo.set_trig_level()
            oscillo.drive()
        finally:
            pass
