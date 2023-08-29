from syndesi.adapters import IP, VISA, IAdapter
from syndesi.protocols.scpi import SCPI
from typing import Union, List
from enum import Enum
from syndesi.tools.types import is_number

class Function(Enum):
    SINUSOID = 'StairDown'
    SQUARE = 'SQU'
    RAMP = 'RAMP'
    PULSE = 'PULS'
    PRNOISE = 'PRN'
    DC = 'DC'
    ARBITRARY = 'EFIL'

class Unit(Enum):
    VPP = 'VPP'
    VRMS = 'VRMS'
    DBM = 'DBM'

HIGH_IMPEDANCE_KEYWORD = 'INF'

class AFG1022:
    def __init__(self, adapter: IAdapter) -> None:
        """
        Tektronix AFG1022 Arbitrary waveform generator

        Parameters
        ----------
        adpater : IAdapter
        """
        super().__init__()

        assert isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter, end='\n')

    def _check_channel(self, channel : int):
        """
        Check the channel type and value
        """
        assert isinstance(channel, int), f"Invalid channel type : {type(channel)}"
        assert 1 <= channel <= 2, f"Invalid channel value : {channel}"

    def set_output_state(self, channel : int, state : bool):
        """
        Set the output state for the desired channel
        
        Parameters
        ----------
        channel : int
        state : bool
        """
        self._check_channel(channel)
        self._prot.write(f'OUTP{channel} {"ON" if state else "OFF"}')

    def set_frequency_sync(self, source_channel : int, state : bool):
        """
        Enable or disable frequency sync (concurrent mode),
        the specified source_channel's frequency is copied on the other one

        Parameters
        ----------
        source_channel : int
        state : bool
        """
        self._check_channel(source_channel)
        self._prot.write(f'SOUR{source_channel}:FREQ_CONC {"ON" if state else "OFF"}')

    def set_frequency(self, channel : int, frequency : float):
        """
        Sets the frequency of output waveform for the specified
        channel.
        This command is available when the Run Mode is set to other than Sweep.

        Parameters
        ----------
        channel : int
        frequency : float
        """
        self._check_channel(channel)
        assert is_number(frequency), f"Invalid frequency type : {type(frequency)}"
        self._prot.write(f'SOUR{channel}:FREQ {frequency}')

    def set_function(self,
                     channel : int,
                     function : Function,
                     name : str = None):
        """
        Set the waveform function for the desired channel

        Parameters
        ----------
        function : Function
        channel : int
        name : str
            For user mode only, name of waveform file or 'VOLATILE'
        """
        self._check_channel(channel)
        assert isinstance(function, Function), f"Invalid function type : {type(function)}"
        # TODO : Add built-ins
        if function == Function.USER:
            if name is not None:
                self._prot.write(f'SOUR{channel}:FUNC EFIL {name}')
            else:
                raise ValueError("waveform name cannot be None")
        else:
            self._prot.write(f'SOUR{channel}:FUNC {function.value}')

    def set_phase(self, channel : int, phase : float, degrees : bool = False):
        """
        Set the phase of the desired channel

        Parameters
        ----------
        channel : int
        phase : float
        degrees : bool
            True : use degrees
            False (default) : use radians
        """
        self._check_channel(channel)
        assert is_number(phase), f"Invalid phase type : {type(phase)}"
        self._prot.write(f'SOUR{channel}:PHAS {phase}{"DEG" if degrees else "RAD"}')

    def set_amplitude_offset(self, channel : int, amplitude : float, offset : float):
        """
        Set the amplitude and offset voltage for the desired channel

        Parameters
        ----------
        channel : int
        amplitude : float
        offset : float
        """
        self._check_channel(channel)
        for n, v in [('amplitude', amplitude), ('offset', offset)]:
            assert is_number(v), f'Invalid {n} type : {type(v)}'
        # Set low voltage
        self._prot.write(f'SOUR{channel}:VOLT:AMPL {amplitude}')
        self._prot.write(f'SOUR{channel}:VOLT:OFFS {offset}')

    def set_low_high(self, channel : int, low : float, high : float):
        """
        Set the low and high voltage values for the desired channel

        Parameters
        ----------
        channel : int
        low : float
        high : float
        """
        self._check_channel(channel)
        assert high >= low, f'Invalid low-high combination : {low}, {high}'
        self.set_amplitude_offset(channel, high - low, (low + high) / 2)

    #########################################################################    

    def set_frequency_sweep(self, channel : int, start : float, stop : float):
        """
        Set the frequency sweep for the desired channel

        Parameters
        ----------
        channel : int
        start : float
        stop : float
        """
        self._check_channel(channel)
        for n, s in [('start', start), ('stop', stop)]:
            assert is_number(s), f"Invalid {n} type : {type(s)}"
        cmd = 'FREQ' + ('' if channel == 1 else ':CH2')
        self._prot.write(f'{cmd}:STAR {start}')
        self._prot.write(f'{cmd}:STOP {stop}')

    def set_output_load(self, channel : int, load : Union[float, str]):
        """
        Sets the output impedance of the specified channel

        Parameters
        ----------
        channel : int
        load : float or str
            Ohm value or 'INF' for high impedance
        """
        self._check_channel(channel)
        cmd = 'OUTP:LOAD' + '' if channel == 1 else ':CH2'
        if isinstance(load, str):
            assert load.upper() == HIGH_IMPEDANCE_KEYWORD, f"Invalid high-impedance value for load : {load}"
            self._prot.write(f'{cmd} {HIGH_IMPEDANCE_KEYWORD}')
        elif is_number(load):
            self._prot.write(f'{cmd} {load}')
        else:
            raise ValueError(f"Invalid load type : {type(load)}")
        
    def set_output_polarity(self, channel : int, normal_nReversed : bool):
        """
        Sets the output polarity for the specified channel

        Parameters
        ----------
        channel : int
        normal_nReversed : bool 
            True : normal
            False : reversed
        """
        self._check_channel(channel)
        cmd = 'OUTP:POL' + '' if channel == 1 else ':CH2'
        self._prot.write(f'{cmd} {"NORM" if normal_nReversed else "INV"}')
    
    def set_output_sync(self, enabled : bool):
        """
        Enables of disables output sync (rear connector).
        This is only available for CH1

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'OUTP:SYNC {"ON" if enabled else "OFF"}')

    def set_output_trigger_slope(self, positive : bool):
        """
        Select the edge of trigger output. If enabled, TTL-compatible
        square wave with specified edge will be generated from the [Ext
        Trig/FSK/Burst] connector on the rear panel when the sweep
        starts.

        Parameters
        ----------
        positive : bool
            True : Rising edge
            False : Falling edge
        """
        self._prot.write(f'OUTP:TRIG:SLOP {"POS" if positive else "NEG"}')
    
    def set_output_trigger(self, enabled : bool):
        """
        Enables or disables output trigger on the [Ext Trig/FSK/Burst]
        connector on the rear panel when the sweep
        starts.
        
        Parameters
        ----------
        enabled : bool        
        """
        self._prot.write(f'OUTP:TRIG {"ON" if enabled else "OFF"}')