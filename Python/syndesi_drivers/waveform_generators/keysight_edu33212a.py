from syndesi.adapters import IP, VISA, IAdapter
from syndesi.protocols.scpi import SCPI
from typing import Union
from enum import Enum
from syndesi.tools.types import is_number

class Function(Enum):
    SINUSOID = 'SIN'
    SQUARE = 'SQU'
    TRIANGLE = 'TRI'
    RAMP = 'RAMP'
    PULSE = 'PULS'
    NOISE = 'NOIS'
    PRBS = 'PRBS'
    DC = 'DC'
    ARBITRARY = 'ARB'

class Unit(Enum):
    VPP = 'Vpp'
    VRMS = 'Vrms'
    DBM = 'dBm'

class SyncMode(Enum):
    NORMAL = 'NORM'
    CARRIER = 'CARR'
    MARKER = 'MARK'

class Polarity(Enum):
    NORMAL = 'NORM'
    INVERTED = 'INV'

HIGH_IMPEDANCE_KEYWORD = 'HIGH'

# All functions were tested on 25.09.2023

class EDU33212A:
    def __init__(self, adapter: IAdapter) -> None:
        """
        Keysight EDU33212A arbitrary waveform generator
        Parameters
        ----------
        adpater : IAdapter
        """
        super().__init__()

        assert isinstance(adapter, (VISA, IP)), "Invalid adapter"
        self._prot = SCPI(adapter, end='\n')

    def test(self):
        """
        Test presence of the device
        Returns
        -------
        True if the device is present
        False if the device doesn't respond or it is the wrong device
        """
        output = self._prot.query('*IDN?')
        # Output is typically :
        # Keysight Technologies,EDU33212A,CN63210021,K-01.03.04-01.00-01.04-01.00-01.00
        return "EDU33212A" in output

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

    def configure_sync_output(self,
                                state : bool,
                                source_channel : int,
                                mode : SyncMode = SyncMode.NORMAL,
                                polarity : Polarity = Polarity.NORMAL):
        """
        Configure the SYNC output
        Parameters
        ----------
        state : bool
            Enable / disables the sync output
        source_channel : int
        mode : SyncMode
        polarity : Polarity
        """
        self._check_channel(source_channel)
        assert isinstance(mode, SyncMode), f"Invalid mode type : {type(mode)}"
        assert isinstance(polarity, Polarity), f"Invalid polarity type : {type(polarity)}"

        self._prot.write(f'OUTP:SYNC:SOUR CH{source_channel}')
        self._prot.write(f'OUTP{source_channel}:SYNC:MODE {mode.value}')
        self._prot.write(f'OUTP{source_channel}:SYNC:POL {polarity.value}')
        self._prot.write(f'OUTP:SYNC {"ON" if state else "OFF"}')

    def sync_phase(self):
        """
        Do a phase sync between CH1 and CH2
        """
        self._prot.write('PHAS:SYNC')

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
                     duty_cycle : Union[float, None] = None):
        """
        Set the waveform function for the desired channel
        Parameters
        ----------
        function : Function
        channel : int
        duty_cycle : float
            Duty-cycle in percent (pulse and square modes only)
        """
        self._check_channel(channel)
        assert isinstance(function, Function), f"Invalid function type : {type(function)}"


        self._prot.write(f'SOUR{channel}:FUNC {function.value}')

        if function in [Function.PULSE, Function.SQUARE] and duty_cycle is not None:
            self._prot.write(f'SOUR{channel}:FUNC:{function.value}:DCYC {duty_cycle}')

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

    def set_amplitude_offset(self, channel : int, amplitude : float, offset : float, unit : Unit = Unit.VPP):
        """
        Set the amplitude and offset voltage for the desired channel
        Parameters
        ----------
        channel : int
        amplitude : float
        offset : float
        unit : Unit
            Volts unit, Vpp by default
        """
        self._check_channel(channel)
        assert isinstance(unit, Unit), f"Invalid unit type : {type(unit)}"
        for n, v in [('amplitude', amplitude), ('offset', offset)]:
            assert is_number(v), f'Invalid {n} type : {type(v)}'
        # Set low voltage
        self._prot.write(f'SOUR{channel}:VOLT:AMPL {amplitude}{unit.value}')
        self._prot.write(f'SOUR{channel}:VOLT:OFFS {offset}')

    def set_low_high(self, channel : int, low : float, high : float, unit : Unit = Unit.VPP):
        """
        Set the low and high voltage values for the desired channel
        Parameters
        ----------
        channel : int
        low : float
        high : float
        unit : Unit
            Volts unit, Vpp by default
        """
        self._check_channel(channel)
        assert high >= low, f'Invalid low-high combination : {low}, {high}'
        self.set_amplitude_offset(channel, high - low, (low + high) / 2, unit=unit)

    def set_output_load(self, channel : int, load):
        """
        Sets the output impedance of the specified channel
        Parameters
        ----------
        channel : int
        load : float/str
            Value or HIGH
        """
        self._check_channel(channel)
        if isinstance(load, str) and load.upper() == 'HIGH':
            # Set high impedance
            self._prot.write(f'OUTP{channel}:LOAD INF')
        else:
            assert isinstance(load, float) or isinstance(load, int), f"Invalid load type : {type(load)}"
            self._prot.write(f'OUTP{channel}:LOAD {load}')