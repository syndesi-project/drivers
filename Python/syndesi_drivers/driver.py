from abc import ABC, abstractclassmethod
from syndesi.protocols import Protocol


class Driver(ABC):
    _prot : Protocol
    @abstractclassmethod
    def test(self):
        """
        Test presence and/or well functionning of the device.

        This function should be implemented using an exchange capable of detecting :
        - Device presence
        - Response to desired queries
        - Distinguish between similar devices (if this is desirable and possible)
        
        Returns
        -------
        True if the device is present and responds correctly
        False otherwise
        """
        pass