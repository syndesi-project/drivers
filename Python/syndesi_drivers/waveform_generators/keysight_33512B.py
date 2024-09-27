from syndesi.adapters import IP, VISA
from syndesi.protocols.scpi import SCPI
from syndesi.tools.types import assert_number

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
        adpater : Adapter
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
    
    def set_arbitrary_file(self, channel : int, filename : str):
        """
        Selects an arbitrary waveform (.arb/.barb) or sequence (.seq) that has
        previously been loaded into volatile memory for the channel specified
        with load_arbitrary_waveform or load_memory_to_volatile

        Parameters
        ----------
        channel : int
        filename : str
        """
        self._check_channel(channel)
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

    def set_dc_value(self, channel : int, value : float, unit : str = VOLT_UNITS[0]):
        """
        Set the DC voltage value
        Parameters
        ----------
        channel : int
        value : float
        unit : str
            VPP, VRMS or DBM
        """
        self._prot.write(f'SOUR{channel}:VOLT:UNIT {unit}')
        self._check_channel(channel)
        assert_number(value)
        self._prot.write(f'SOUR{channel}:VOLT:OFFS {value}')

    def set_amplitude_offset(self, channel : int, amplitude : float, offset : float, unit=VOLT_UNITS[0]):
        """
        Sets the amplitude and offset of the specified channel

        Cannot be used for setting DC value, use .set_dc_value(channel, value)

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


    def set_autorange(self, channel : int, state : bool):
        """
        Enable or disable autoranging on the specified channel
        To set a desired range
        - set the output state to False
        - enable autoranging
        - configure the maximum voltage range
        - disable autoranging
        Parameters
        ----------
        channel : int
        state : bool
        """
        self._check_channel(channel)
        self._prot.write(f'SOUR{channel}:VOLT:RANG:AUTO {"ON" if state else "OFF"}')

    def get_volatile_catalog(self, channel):
        """
        Returns the contents of volatile waveform memory, including arbitrary
        waveforms and sequences for the specified channel

        Parameters
        ----------
        channel : int
        """
        # Output like : '"EXP_RISE","TEST"'
        self._check_channel(channel)
        output = self._prot.query(f'SOUR{channel}:DATA:VOL:CAT?')
        catalog = []
        if ',' in output:
            catalog += [x.replace('"', '') for x in output.split(',')]
        return catalog
    
    def clear_volatile_memory(self, channel : int):
        """
        Clears waveform memory for the specified channel and reloads the default waveform.
        
        Parameters
        ----------
        channel : int
        """
        self._prot.write(f'SOUR{channel}:DATA:VOL:CLE')

    def load_arbitrary_waveform(self, channel : int, name : str, points : list, dac=False, overwrite=False):
        """
        Downloads integer values representing DAC codes between -32768 and +32767(dac=True)
        or floating point values (dac=False) into waveform volatile memory
        Load an arbitrary waveform in memory

        Call load_from_memory()

        Parameters
        ----------
        channel : int
        name : str
            Name of the arbitrary waveform
        points : list or np.array
        dac : bool
            True : points are raw DAC values (-32768 to 32767)
            False (default) : points are -1.0 to +1.0
        overwrite : bool
            Overwrite existing file
        """
        self._check_channel(channel)
        # Check if the file already exists (all names are uppercased)
        if name.upper() in self.get_volatile_catalog(channel):
            if overwrite:
                self.clear_volatile_memory(channel)
            else:
                raise RuntimeError(f"File {name} already exists. To ignore, set overwrite=True")

        RANGE = (-32767, 32767) if dac else (-1.0, 1.0)
        assert min(points) >= RANGE[0] and max(points) <= RANGE[1], f"Invalid points range ({min(points)} to {max(points)})"
        command = f'SOUR{channel}:DATA:ARB'
        if dac:
            command += ':DAC'
            points_list = [f'{p:.0f}' for p in points]
        else:
            points_list = [f'{p}' for p in points]
        command += f' {name},{",".join(points_list)}'
        self._prot.write(command)

    def load_memory_to_volatile(self, channel : int, path : str):
        """
        Loads the specified arb segment(.arb/.barb) or arb sequence (.seq) file in INTERNAL or USB memory into
        volatile memory for the specified channel.
        """
        self._check_channel(channel)
        self._prot.write(f'MMEM:LOAD:DATA{channel} \"{path}\"')


    def set_burst_state(self, channel : int, state : bool, mode : str = 'triggered', n_cycles : int = 1, start_phase : float = 0, burst_period : float = None):
        """
        Enables or disables burst mode.

        Output phase is set to 0 when burst is enabled.

        Set the trigger source with set_trigger_source

        Parameters
        ----------
        channel : int
        state : bool
        mode : str
            'triggered' or 'gated'
        n_cycles : int
            Number of cycles
        """
        self._check_channel(channel)
        self._prot.write(f'SOUR{channel}:BURS:STAT {1 if state else 0}')
        if state:
            assert mode in ['triggered', 'gated'], f"Invalid mode : {mode}"
            self._prot.write(f'SOUR{channel}:BURS:MODE {mode}')
            self._prot.write(f'SOUR{channel}:BURS:NCYC {n_cycles}')
            self._prot.write(f'SOUR{channel}:BURS:PHAS {start_phase}')
            if burst_period is not None:
                self._prot.write(f'SOUR{channel}:BURS:INT:PER {burst_period}')

    def set_trigger_source(self, channel : int, source : str):
        """
        Selects the trigger source for sequence, list, burst or sweep. The instrument accepts an immediate or
        timed internal trigger, an external hardware trigger from the rear-panel Ext Trig connector, or a software
        (bus) trigger.
        
        Parameters
        ----------
        channel : int
        source : str
            'immediate', 'external', 'timer' or 'bus'
        """
        self._check_channel(channel)
        assert source in ['immediate', 'external', 'timer', 'bus']
        self._prot.write(f'TRIG{channel}:SOUR {source}')

    def set_arbitrary_sample_rate(self, channel : int, sample_rate : float):
        """
        Sets the sample rate for the arbitrary waveform.

        Parameters
        ----------
        channel : int
        sample_rate : float
        """
        self._check_channel(channel)
        self._prot.write(f'SOUR{channel}:FUNC:ARB:SRAT {sample_rate}')
            
    def sync_phase(self):
        """
        Simultaneously resets all phase generators in the instrument, including the modulation phase
        generators, to establish a common, internal phase zero reference point. This command does not affect
        PHASe setting of either channel; it simply establishes phase difference between channels as the sum of
        channel 1 and channel 2 sources.
        """
        self._prot.write('PHAS:SYNC')