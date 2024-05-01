from abc import ABC, abstractmethod
from syndesi.tools.types import assert_number

class PowersupplyDC(ABC):
    def __init__(self, channel_number : int = None) -> None:
        """
        Single channel power supply (or a specific channel of a multi-channel power supply)

        Parameters
        ----------
        channel_number : int
            Channel in the case of this instance being a specific channel of a multi-channel power supply (None by default)
        """
        super().__init__()
        self._channel_number = channel_number
        
    @abstractmethod
    def set_voltage(self, volts : float):
        pass
    
    @abstractmethod
    def get_voltage(self) -> float:
        pass
    
    @abstractmethod
    def set_current(self, amps : float):
        pass
    
    @abstractmethod
    def get_current(self) -> float:
        pass
    
    @abstractmethod
    def set_output_state(self, state : bool):
        pass
    
    @abstractmethod
    def measure_dc_voltage(self) -> float:
        pass
    
    @abstractmethod
    def measure_dc_current(self) -> float:
        pass

class MultiChannelPowersupplyDC(ABC):
    # Provides power supply functions (multi channel)

    def __init__(self, n_channels : int) -> None:
        ABC.__init__(self) # TODO : Check if this is the right way
        self._n_channels = n_channels

    def _check_channel(self, channel):
        assert_number(channel)
        assert 1 <= channel <= self._n_channels, f"Invalid channel number : {channel}"

    @abstractmethod
    def channel(self, channel_number : int) -> PowersupplyDC:
        pass