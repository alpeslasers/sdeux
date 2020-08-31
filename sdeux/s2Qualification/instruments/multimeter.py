
from dms import DMSManager


class MultiMeter:

    def __init__(self, th):
        self.th = th

    def set_up(self):
        pass

    def get_voltage(self):
        return float(self.th.query("MEAS:VOLT?"))

    def get_current(self):
        return float(self.th.query("MEAS:CURR?"))

if __name__ == '__main__':
    dms = DMSManager()
    mm_th = dms.get_instrument('HP/S2/INSTRUMENTS/CHIPIX-AL_200252')
    with dms.acquire_instruments(mm_th):
        mm = MultiMeter(mm_th)
        mm.set_up()
        print(mm.get_voltage())
        # print(mm.get_current())

