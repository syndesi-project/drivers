from abc import ABC, abstractmethod

class Voltmeter(ABC):
    # Provides a voltage measurement
    @abstractmethod
    def measure_dc_voltage(self) -> float:
        pass
    
    @abstractmethod
    def measure_ac_voltage(self) -> float:
        pass

class Ammeter(ABC):
    # Provides a current measurement
    @abstractmethod
    def measure_dc_current(self) -> float:
        pass
    
    @abstractmethod
    def measure_ac_current(self) -> float:
        pass

class Ohmmeter(ABC):
    # Provides a resistance measurement
    @abstractmethod
    def measure_resistance(self) -> float:
        """
        2-wire measurement is implied
        """
        pass

# Multimeter combines Voltmeter, Ammeter and OhmMeter
class Multimeter(Voltmeter, Ammeter, Ohmmeter):
    pass