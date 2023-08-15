from .. import IAmmeter, IVoltmeter
from syndesi.adapters import IAdapter, IP, VISA
from syndesi.protocols import SCPI

# https://int.siglent.com/upload_file/user/SDM3055/SDM3055_RemoteManual_RC06035-E01A.pdf

class SDM3055(IVoltmeter, IAmmeter):
    def __init__(self, adapter : IAdapter) -> None:
        """
        Siglent SDM3055 5½ digit multimeter

        Parameters
        ----------
        adpater : IAdapter
            Adapter to use, both IP and VISA are allowed
        """
        super().__init__()

        assert isinstance(adapter, IP) or isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter)

    def measure_ac_current(self) -> float:
        """
        Make an AC current measurement and return the result
        """
        self._prot.write('CONF:CURR:AC')
        self._prot.write('INIT')
        self._prot.write('*TRG')
        output = float(self._prot.query('FETC?'))
        return output

    def measure_dc_current(self) -> float:
        """
        Make a DC current measurement and return the result
        """
        self._prot.write('CONF:CURR:DC')
        self._prot.write('INIT')
        self._prot.write('*TRG')
        output = float(self._prot.query('FETC?'))
        return output

    def measure_ac_voltage(self) -> float:
        """
        Make an AC voltage measurement and return the result
        """
        self._prot.write('CONF:VOLT:AC')
        self._prot.write('INIT')
        self._prot.write('*TRG')
        output = float(self._prot.query('FETC?'))
        return output

    def measure_dc_voltage(self) -> float:
        """
        Make a DC voltage measurement and return the result
        """
        self._prot.write('CONF:VOLT:DC')
        self._prot.write('INIT')
        self._prot.write('*TRG')
        output = float(self._prot.query('FETC?'))
        return output