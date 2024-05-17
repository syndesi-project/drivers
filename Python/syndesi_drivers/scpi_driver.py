# scpi_driver.py
# Sébastien Deriaz
# 27.04.2023
#
# 
from .driver import Driver
from syndesi.adapters import Adapter
from syndesi.protocols import SCPI

class SCPIDriver(Driver):
    def __init__(self, adapter : Adapter) -> None:
        super().__init__()

        self._prot = SCPI(adapter)

    # Standard SCPI commands
    def get_identification(self):
        """
        Return identification returned by '*IDN?'

        Returns
        -------
        identification : str
        """
        identification = self._prot.query('*IDN?')
        return identification
    
    def get_system_error(self):
        """
        Return the last error issued by the instrument

        Returns
        -------
        error : str
        """
        return self._prot.query('SYST:ERR?')

    def get_version(self):
        """
        Get the software version of the equipment

        Returns
        -------
        version : str
        """
        return self._prot.query('SYST:VERS?')

    def clear_status(self):
        """
        Clear event registers as well as error queue
        """
        self._prot.write('*CLS')

    def reset(self):
        """
        Reset the instrument to factory state
        """
        self._prot.write('*RST')