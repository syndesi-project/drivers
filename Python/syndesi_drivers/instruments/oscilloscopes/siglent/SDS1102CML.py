# Siglent SDS1102CML oscilloscope driver
# Sébastien Deriaz
# 30.05.2023

from .. import IOscilloscope
from syndesi.adapters import IAdapter, Serial, USBVisa
from ....protocols import SCPI

class SDS1102CML(IOscilloscope):
    def __init__(self, adapter : IAdapter) -> None:
        super().__init__()


        assert isinstance(adapter, Serial) or isinstance(adapter, USBVisa), "Invalid adapter"
        self._prot = SCPI(adapter)

    def set_time_scale(self, seconds_per_div : float):
        pass

    def set_voltage_scale(self, channel : int, volts_per_div : float):
        pass

    def set_coupling(self, channel : int, coupling : IOscilloscope.Coupling):
        pass