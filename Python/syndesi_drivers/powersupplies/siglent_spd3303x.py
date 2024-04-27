# Siglent SPD3303X-E and SPD3303X power supply drivers
# Sébastien Deriaz
# 02.04.2023


from syndesi.protocols import SCPI, Protocol
from . import MultiChannelPowersupplyDC, PowersupplyDC
from syndesi.adapters import *
from packaging.version import Version
from typing import Union
from enum import Enum
from syndesi.tools.types import assert_number
from dataclasses import dataclass
import struct

DEFAULT_TIMEOUT = Timeout(0.2, 0.1)


class ChannelMode(Enum):
    CONSTANT_VOLTAGE = 0
    CONSTANT_CURRENT = 1
    

class OperationMode(Enum):
    INDEPENDENT = 'independant'
    SERIES = 'series'
    PARALLEL = 'parallel'

_operation_mode_id = {
    OperationMode.INDEPENDENT : 0,
    OperationMode.SERIES : 1,
    OperationMode.PARALLEL : 2
}

@dataclass
class SystemStatus:
    channel1_mode : ChannelMode
    channel2_mode : ChannelMode
    operation_mode : OperationMode
    channel1_enabled : bool
    channel2_enabled : bool
    timer1_enabled : bool
    timer2_enabled : bool
    channel1_waveform_display : bool
    channel2_waveform_dislpay : bool

class SiglentSPD3303xChannel(PowersupplyDC):
    VERSION = Version('1.0.0')
    def __init__(self, adapter : Union[Adapter, Protocol], channel_number: int = None) -> None:
        super().__init__(channel_number)
        if isinstance(adapter, Protocol):
            self._prot = adapter
        else:
            adapter.set_default_timeout(DEFAULT_TIMEOUT)
            self._prot = SCPI(adapter)


    def measure_dc_current(self) -> float:
        """
        Return current measurement

        Returns
        -------
        current : float
        """
        output = self._prot.query(f'MEAS:CURR? CH{self._channel_number}')
        return float(output)
    
    def measure_dc_voltage(self) -> float:
        """
        Return voltage measurement

        Returns
        -------
        voltage : float
        """
        output = self._prot.query(f'MEAS:VOLT? CH{self._channel_number}')
        return float(output)
    
    def measure_dc_power(self) -> float:
        """
        Return power measurement
        
        Returns
        -------
        power : float
        """
        output = self._prot.query(f'MEAS:POW? CH{self._channel_number}')
        return float(output)
    


    def set_voltage(self, volts : float):
        self._prot.write(f'CH{self._channel_number}:VOLT {volts:.3f}')

    def get_voltage(self) -> float:
        self._prot.write(f'CH{self._channel_number}:VOLT?')
        output = self._prot.read()
        try:
            volts = float(output)
        except ValueError as e:
            volts = None
        return volts
    
    def set_current(self, amps : float):
        self._prot.write(f'CH{self._channel_number}:CURR {amps:.3f}')

    def get_current(self) -> float:
        self._prot.write(f'CH{self._channel_number}:CURR?')
        output = self._prot.read()
        try:
            amps = float(output)
        except ValueError as e:
            amps = None
        return amps

    def set_output_state(self, state : bool):
        self._prot.write(f'OUTP CH{self._channel_number} {"ON" if state else "OFF"}')

    def set_wave_display(self, state : bool):
        """
        Enable/disable the wave display
        """
        self._prot.write(f'OUTP:WAVE CH{self._channel_number},{"ON" if state else "OFF"}')

    def set_timer(self, group, voltage, current, time):
        """
        Set timing parameters, including group(1-5), voltage, current and time

        Parameters
        ----------
        voltage : float or list
        current : float or list
        time : float or list
        """
        if all([isinstance(x, float) for x in [group, voltage, current, time]]):
            # Make lists
            group = [group]
            voltage = [voltage]
            current = [current]
            time = [time]
        elif not all([isinstance(x, list) for x in [group, voltage, current, time]]):
            raise ValueError(f"Invalid input types")
        
        for g, v, c, t in zip(group, voltage, current, time):
            assert 1 <= g <= 5, f'Invalid group value : {g}'
            self._prot.write(f'TIME:SET CH{self._channel_number},{g},{v},{c},{t}')
    
    def get_timer(self, group):
        """
        Query the voltage/current/time parameters of specified group
        
        Parameters
        ----------
        group : int

        Returns
        -------
        voltage : float
        current : float
        time : float
        """
        # TODO

    def get_mode(self):
        """
        Return channel mode (constant voltage or constant current)

        Returns
        -------
        mode : ChannelMode
        """
        # TODO : Find a way to get the mode here (even though it is declared in the main SPD3303X class)
        


class SiglentSPD3303x(MultiChannelPowersupplyDC):
    VERSION = Version('1.0.0')
    def __init__(self, adapter : Adapter) -> None:
        super().__init__(2)

        assert isinstance(adapter, VISA) or isinstance(adapter, IP), "Invalid adapter"

        self._prot = SCPI(adapter)

    def channel(self, channel_number: int) -> SiglentSPD3303xChannel:
        return SiglentSPD3303xChannel(self._prot, channel_number=channel_number)

    def set_operation_mode(self, mode : OperationMode):
        """
        Set the operation mode

        Parameters
        ----------
        mode : OperationMode or str
            'independant', 'series' or 'parallel'
        """
        mode = OperationMode(mode)
        _id = _operation_mode_id[mode]
        self._prot.write(f'OUTP:TRACK {_id}')

    def _check_save_id(self, save_id : int):
        assert_number(save_id)
        assert 1 <= save_id <= 5, f'Invalid save_id value : {save_id}'

    def save(self, save_id : int):
        """
        Save current state in nonvolatile memory

        Parameters
        ----------
        save_id : int
            Save index [1-5]
        """
        self._check_save_id(save_id)
        self._prot.write(f'*SAV {save_id}')

    def recall(self, save_id : int):
        """
        Recall state that had been saved from nonvolatile memory

        Parameters
        ----------
        save_id : int
            Save index [1-5]
        """
        self._check_save_id(save_id)
        self._prot.write(f'*RCL {save_id}')

    def select_instrument_channel(self, channel_number : int):
        """
        Select the channel that will be operated. This is not necessary to use either channel with this driver

        Parameters
        ----------
        channel_number : int
        """
        self._check_channel(channel_number)
        self._prot.write(f'INST CH{channel_number}')

    def get_instrument_channel(self):
        """
        Return the selected channel

        Returns
        -------
        channel_number : int
        """
        # output : CHx
        output = self._prot.query('INST?')
        channel_number = int(output.strip('CH'))
        return channel_number

    def measure_total_dc_power(self):
        """
        Return sum of both channel power

        Returns
        -------
        power : float
        """
        output = sum([self.channel(i+1).measure_dc_power() for i in range(self._n_channels)])
        return output
    
    

    def get_system_status(self):
        """
        Query the current working state of the equipment

        Returns
        -------
        status : SystemStatus
        """
        # TODO : Parse with struct
