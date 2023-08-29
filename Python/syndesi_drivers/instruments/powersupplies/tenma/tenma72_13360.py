from syndesi.adapters import Serial
from syndesi.protocols.delimited import Delimited
from syndesi_drivers.instruments.powersupply import IPowersupplyDC
from typing import Union, List
from enum import Enum
from syndesi.tools.types import is_number


class Tenma72_13360(IPowersupplyDC):
    def __init__(self, adapter: Serial) -> None:
        """
        Tenma 72-13360 30V 15A power supply

        Parameters
        ----------
        adpater : IAdapter
        """
        super().__init__()

        assert isinstance(adapter, Serial), "Invalid adapter"
        self._prot = Delimited(adapter, termination='\n')

    
    def set_current(self, amps: float):
        """
        Set the power supply current
        
        Parameters
        ----------
        amps : float
        """
        self._prot.write(f'ISET:{amps}')

    def get_current(self) -> float:
        """
        Get the current setpoint

        Returns
        -------
        amps : float
        """
        return float(self._prot.query('ISET?'))
    
    def set_voltage(self, volts: float):
        """
        Set the power supply voltage
        
        Parameters
        ----------
        volt : float
        """
        assert is_number(volts), f"Invalid volts type : {type(volts)}"
        self._prot.write(f'VSET:{volts}')

    def get_voltage(self) -> float:
        """
        Get the voltage setpoint

        Returns
        -------
        volts : float
        """
        return float(self._prot.query('VSET'))
    
    def measure_dc_current(self) -> float:
        """
        Return the output current measurement

        Returns
        -------
        amps : float
        """
        return float(self._prot.query('IOUT?'))
    
    def measure_dc_voltage(self) -> float:
        """
        Return the output voltage measurement

        Returns
        -------
        volts : float
        """
        return float(self._prot.query('VOUT?'))
    
    def set_beep_state(self, enabled : bool):
        """
        Enable or disable the beep

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'BOOP:{1 if enabled else 0}')
    
    def set_output_state(self, state: bool):
        """
        Set the output state

        Parameters
        ----------
        state : bool
        """
        self._prot.write(f'OUT:{1 if state else 0}')
    
    def set_overcurrent_protection(self, amps : float):
        """
        Set the overcurrent protection value

        Parameters
        ----------
        amps : float
        """
        assert is_number(amps), f"Invalid amps type : {type(amps)}"
        self._prot.write(f'OCP:{amps}')

    def set_overvoltage_protection(self, volts : float):
        """
        Set the overvoltage protection value

        Parameters
        ----------
        volts : float
        """
        assert is_number(volts), f"Invalid volts type : {type(volts)}"
        self._prot.write(f'OVP:{volts}')

    def set_voltage_slope(self, slope : float):
        """
        Set the voltage slope as V/100us

        Parameters
        ----------
        slope : float        
        """
        assert is_number(slope), f"Invalid slope type : {type(slope)}"
    
    def set_lock(self, enabled : bool):
        """
        Enable or disable the front panel lock

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'LOCK:{1 if enabled else 0}')

    def set_external_trigger(self, enabled : bool):
        """
        Enable or disable the external trigger

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'EXIT:{1 if enabled else 0}')