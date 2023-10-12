from syndesi.adapters import IP, VISA
from syndesi.protocols.scpi import SCPI

# https://www.keysight.com/fr/en/assets/9018-03714/service-manuals/9018-03714.pdf?success=true


WAVEFORM_FUNCTIONS = ['SIN', 'SQU', 'TRI', 'RAMP', 'PULS', 'PRBS', 'ARB', 'DC']
VOLT_UNITS = ['VPP', 'VRMS', 'DBM']
ANGLE_UNITS = ['DEG', 'RAD', 'SEC']
HIGH_IMPEDANCE_KEYWORD = "HIGH"

class Keysight33512B:
    def __init__(self, adapter: IP) -> None:
        """
        Keysight 33500B Trueform Series Waveform Generator

        Parameters
        ----------
        adpater : IAdapter
        """
        super().__init__()

        assert isinstance(adapter, IP) or isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter)

    def set_frequency_coupling(self, enabled : bool, ratio=None, offset=None):
        """
        Sets the frequency coupling mode

        Set either ratio or offset, not both

        Parameters
        ----------
        enabled : bool
        ratio : float
        offset : float
        """
        if enabled:
            self._prot.write(f'FREQ:COUP ON')
            if ratio is None and offset is None:
                raise ValueError("offset and ratio cannot be both None")
            elif ratio is not None and offset is not None:
                raise ValueError("offset and ratio cannot be set at the same time")
            elif ratio is not None:
                # Set the ratio
                assert isinstance(ratio, int) or isinstance(ratio, float), f"Invalid ratio type : {type(ratio)}"
                self._prot.write('FREQ:COUP:MODE RAT')
                self._prot.write(f'FREQ:COUP:RAT {ratio}')
            else:
                # Set the offset
                assert isinstance(offset, int) or isinstance(offset, float), f"Invalid offset type : {type(offset)}"
                self._prot.write('FREQ:COUP:MODE OFFS')
                self._prot.write(f'FREQ:COUP:OFFS {offset}')
        else:
            self._prot.write(f'FREQ:COUP OFF')
            raise ValueError("Set either")
        
    def _check_channel(self, channel):
        assert isinstance(channel, int), f"Invalid channel type : {type(channel)}"
        assert 1 <= channel <= 2, f"Invalid channel number : {channel}"

    def set_waveform_function(self, channel : int, waveform : str):
        """
        Sets the waveform shape of the specified channel, available values are :
            - SIN : Sinusoisdal
            - SQU : Square
            - TRI : Triangle
            - RAMP : Ramp
            - PULS : Pulse
            - PRBS : Pseudo-random noise using LFSR
            - ARB : Arbitrary waveform
            - DC : Constant

        Parameters
        ----------
        channel : int
        waveform : str
        """
        self._check_channel(channel)
        assert waveform in WAVEFORM_FUNCTIONS, f"Invalid waveform : {waveform}"

        self._prot.write(f'SOUR{channel}:FUNC {waveform}')
    
    def set_arbitrary_template(self, channel : int, filename : str):
        """
        Sets the arbitrary template (filename) to use

        Parameters
        ----------
        channel : int
        filename : str
        """
        self._check_channel(channel)
        assert isinstance(filename, str), f"Invalid filename type : {type(filename)}"
        self._prot.write(f'SOUR{channel}:FUNC:ARB {filename}')
        
    def set_frequency(self, channel : int, frequency : float):
        """
        Sets the frequency of the specified channel

        Parameters
        ----------
        channel : int
        frequency : float
        """
        self._check_channel(channel)
        assert isinstance(frequency, float) or isinstance(frequency, int), f"Invalid frequency type : {type(frequency)}"
        self._prot.write(f'SOUR{channel}:FREQ {frequency}')



    def set_amplitude_offset(self, channel : int, amplitude : float, offset : float, unit=VOLT_UNITS[0]):
        """
        Sets the amplitude and offset of the specified channel

        Parameters
        ----------
        channel : int
        amplitude : float
        offset : float
        unit : str
            VPP, VRMS or DBM
        """
        self._check_channel(channel)
        self._check_units(unit)
        self._prot.write(f'SOUR{channel}:VOLT:UNIT {unit}')
        assert isinstance(amplitude, float) or isinstance(amplitude, int), f"Invalid amplitude type : {type(amplitude)}"
        assert isinstance(offset, float) or isinstance(offset, int), f"Invalid offset type : {type(offset)}"

        self._prot.write(f'SOUR{channel}:VOLT:OFFS {offset}')
        self._prot.write(f'SOUR{channel}:VOLT {amplitude}')

    def _check_units(self, unit : str):
        assert unit.upper() in VOLT_UNITS, f"Invalid unit : {unit}"

    def set_low_high(self, channel : int, low : float, high : float, unit=VOLT_UNITS[0]):
        """
        Sets the high and low voltage values of the specified channel

        Parameters
        ----------
        channel : int
        high : float
        low : float
        unit : str
            VPP, VRMS or DBM
        """
        self._check_channel(channel)
        self._check_units(unit)
        self._prot.write(f'SOUR{channel}:VOLT:UNIT {unit}')
        assert isinstance(high, float) or isinstance(high, int), f"Invalid high type : {type(high)}"
        assert isinstance(low, float) or isinstance(low, int), f"Invalid low type : {type(low)}"
        assert low <= high, "low value cannot be lower than high value"
        self._prot.write(f'SOUR{channel}:VOLT:LOW {low}')
        self._prot.write(f'SOUR{channel}:VOLT:HIGH {high}')

    def set_output_load(self, channel : int, load):
        f"""
        Sets the output impedance of the specified channel

        Parameters
        ----------
        channel : int
        load : float/str
            Value or {HIGH_IMPEDANCE_KEYWORD}
        """
        self._check_channel(channel)
        if isinstance(load, str) and load.upper() == HIGH_IMPEDANCE_KEYWORD.upper():
            # Set high impedance
            self._prot.write(f'OUTP{channel}:LOAD INF')
        else:
            assert isinstance(load, float) or isinstance(load, int), f"Invalid load type : {type(load)}"
            self._prot.write(f'OUTP{channel}:LOAD {load}')

    def set_output_state(self, channel : int, state : bool):
        """
        Sets the output state of the desired channel
        
        Parameters
        ----------
        channel : int
        state : bool
        """
        self._check_channel(channel)
        assert isinstance(state, bool) or isinstance(state, int), f"Invalid state type : {type(state)}"
        self._prot.write(f'OUTP{channel} {"ON" if state else "OFF"}')

    def sync_phases(self):
        """
        Syncs the two channels phases, this does not change the phase values
        """
        self._prot.write('PHAS:SYNC')

    def set_phase(self, channel : int, phase : float, unit=ANGLE_UNITS[0]):
        f"""
        Sets the phase of the specified channel
        
        Parameters
        ----------
        channel : int
        phase : float
        unit : str
            DEG, RAD or SEC (seconds), default to {ANGLE_UNITS[0]}
        """
        self._check_channel(channel)
        assert unit.upper() in ANGLE_UNITS
        self._prot.write(f'UNIT:ANGL {unit}')
        assert isinstance(phase, float) or isinstance(phase, int), f"Invalid phase type {type(phase)}"
        self._prot.write(f'SOUR{channel}:PHAS {phase}')

    def get_current_waveform_function(self, channel):
        """
        Return the current waveform function of the specified channel

        Parameters
        ----------
        channel : int        
        """
        self._check_channel(channel)
        return self._prot.query('FUNC?')

    def set_duty_cycle(self, channel : int, duty_cycle : float):
        """
        Sets the duty cycle of the specified channel (square and pulse only)

        Parameters
        ----------
        channel : int
        duty_cycle : float
            Percent
        """
        self._check_channel(channel)
        assert isinstance(duty_cycle, int) or isinstance(duty_cycle, float), f"Invalid duty_cycle type {type(duty_cycle)}"
        assert 0 <= duty_cycle <= 100, f"Invalid duty_cycle value {duty_cycle}"
        func = self.get_current_waveform_function(channel)
        if func not in ['SQU', 'PULS']:
            raise ValueError("Cannot set duty_cycle when not in square or pulse mode")
        self._prot.write(f'SOUR{channel}:FUNC:{func}:DCYCLE {duty_cycle}')

    def test(self):
        """
        Test presence of the device

        Returns
        -------
        success : bool
        """
        output = self._prot.query('*IDN?')
        return '33512B' in output
