from syndesi.adapters import IP, VISA, IAdapter
from syndesi.protocols.scpi import SCPI
from syndesi_drivers.instruments.multimeters import IMultimeter
from syndesi.tools.types import assert_number
from typing import Union, List
from enum import Enum

DEFAULT_NPLC_VALUE = 10
AUTO_RANGE_KEYWORD = 'AUTO'
NPLC_RANGES = [0.02, 0.2, 1, 10, 100]


class Model(Enum):
    _34450A = 1
    _34460A = 2
    _34461A = 3
    _34465A = 4
    _34470A = 5

class Trigger(Enum):
    IMMEDIATE = 'IMM'
    EXTERNAL = 'EXT'
    BUS = 'BUS'
    INTERNAL = 'INT'

class Function(Enum):
        VOLTAGE_DC = 'VOLT:DC'
        VOLTAGE_AC = 'VOLT:AC'
        CURRENT_DC = 'CURR:DC'
        CURRENT_AC = 'CURR:AC'
        RESISTANCE = 'RES'
        RESISTANCE_4WIRE = 'FRES'
        DIODE = 'DIOD'
        CONTINUITY = 'CONT'
        CAPACITANCE = 'CAP'
        FREQUENCY = 'FREQ'
        TEMPERATURE = 'TEMP'

RANGES = {
    Function.VOLTAGE_DC : [100e-3, 1, 10, 100, 1000],
    Function.VOLTAGE_AC : [100e-3, 1, 10, 100, 1000],
    Function.CURRENT_DC : [100e-6, 1e-3, 10e-3, 100e-3, 1, 3, 10],
    Function.CURRENT_AC : [100e-6, 1e-3, 10e-3, 100e-3, 1, 3, 10],
    Function.RESISTANCE : [100, 1e3, 10e3, 100e3, 1e6, 10e6, 100e6, 1e9],
    Function.RESISTANCE_4WIRE : [100, 1e3, 10e3, 100e3, 1e6, 10e6, 100e6, 1e9],
    Function.DIODE : None,
    Function.CONTINUITY : None,
    Function.CAPACITANCE : [1e-9, 10e-9, 100e-9, 1e-6, 10e-6, 100e-6],
    Function.FREQUENCY : None,
    Function.TEMPERATURE : None
}

DEFAULT_RESOLUTION_VALUE = 1.5e-6

class Keysight34xxx(IMultimeter):
    def __init__(self, adapter: IAdapter, model : Model) -> None:
        """
        Keysight 344xxx DMMs, compatible models are :

        - 34550A
        - 34460A
        - 34461A
        - 34465A
        - 34470A

        Parameters
        ----------
        adpater : IAdapter
        model : str
            One of the models above
        """
        super().__init__()
        assert isinstance(model, Model), f"Invalid model type : {type(model)}"
        self._model = model

        assert isinstance(adapter, IP) or isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter, end='\n')

    def _split_comma_separated_floats(self, buffer) -> List[float]:
        """
        Return a single float if there a single one
        Return a list of floats if there are multiple separated by a comma
        """
        if ',' in buffer:
            # Return a list
            return [float(x) for x in buffer.split(',')]
        else:
            return [float(buffer)]

    def measure_ac_current(self, samples=1, rng=AUTO_RANGE_KEYWORD) -> Union[float, List[float]]:
        f"""
        Make an AC current measurement and return the result

        Parameters
        ----------
        samples : int
            Number of samples
        nplc : int/float
            Number of power-line cycles per acquisition (default to {DEFAULT_NPLC_VALUE})
        rng : float/str
            Range setting (default to {AUTO_RANGE_KEYWORD})
        """   
        self.configure_ac_current(samples, rng)

        # TODO : implement timeouts        
        return self.get_measurement()
    
    def measure_dc_current(self, samples=1, nplc=DEFAULT_NPLC_VALUE, rng=AUTO_RANGE_KEYWORD) -> Union[float, List[float]]:
        f"""
        Make an DC current measurement and return the result

        Parameters
        ----------
        samples : int
            Number of samples
        nplc : int/float
            Number of power-line cycles per acquisition (default to {DEFAULT_NPLC_VALUE})
        rng : float/str
            Range setting (default to {AUTO_RANGE_KEYWORD})
        """   
        self.configure_dc_current(samples, nplc, rng)

        # TODO : implement timeouts        
        return self.get_measurement()
    
    def measure_ac_voltage(self, samples=1, rng=AUTO_RANGE_KEYWORD) -> Union[float, List[float]]:
        f"""
        Make an AC voltage measurement and return the result

        Parameters
        ----------
        samples : int
            Number of samples
        nplc : int/float
            Number of power-line cycles per acquisition (default to {DEFAULT_NPLC_VALUE})
        rng : float/str
            Range setting (default to {AUTO_RANGE_KEYWORD})
        """   
        self.configure_ac_voltage(samples, rng)

        # TODO : implement timeouts        
        return self.get_measurement()
    
    def measure_dc_voltage(self, samples=1, nplc=DEFAULT_NPLC_VALUE, rng=AUTO_RANGE_KEYWORD) -> Union[float, List[float]]:
        f"""
        Make an DC voltage measurement and return the result

        Parameters
        ----------
        samples : int
            Number of samples
        nplc : int/float
            Number of power-line cycles per acquisition (default to {DEFAULT_NPLC_VALUE})
        rng : float/str
            Range setting (default to {AUTO_RANGE_KEYWORD})
        """   
        self.configure_dc_voltage(samples, nplc, rng)

        # TODO : implement timeouts        
        return self.get_measurement()

    def measure_resistance(self, samples=1, nplc=DEFAULT_NPLC_VALUE, rng=AUTO_RANGE_KEYWORD) -> Union[float, List[float]]:
        f"""
        Make an resistance measurement and return the result

        Parameters
        ----------
        samples : int
            Number of samples
        nplc : int/float
            Number of power-line cycles per acquisition (default to {DEFAULT_NPLC_VALUE})
        range : float/str
            Range setting (default to {AUTO_RANGE_KEYWORD})
        """
        self.configure_resistance(samples, nplc, rng)

        # TODO : implement timeouts        
        return self.get_measurement()
    
    def get_measurement(self) -> float:
        """
        Return a single measurement, if multiple are configured, only the first one is returned
        """
        return self.get_measurements()[0]
    
    def get_measurements(self) -> List[float]:
        """
        Get the samples from the multimeters, a configure command should be used to set the multimeter beforehand
        If there's a single one, cast it to a list
        """
        self._prot.write('INIT')
        output = self._prot.query('FETC?')
        return self._split_comma_separated_floats(output)

    def test(self):
        """
        Test presence of the device

        Returns
        -------
        success : bool
        """
        output = self._prot.query('*IDN?')
        return '34461A' in output
    

    def set_measurement_function(self,
                                 function : Function,
                                 rng : Union[str, float] = AUTO_RANGE_KEYWORD,
                                 nplc : float = DEFAULT_NPLC_VALUE,
                                 resolution : float = None,
                                 samples : int = 1,
                                 trigger_source : Trigger = Trigger.IMMEDIATE,
                                 trigger_delay : float = None,
                                 trigger_slope : bool = None,
                                 sample_period : float = None
                                 ):
        """
        Selects the measurement function

        - voltage
        - current
        - resistance
        - resistance_4wire
        - diode
        - continuity
        - capacitance
        - frequency
        - temperature

        Parameters
        ----------
        function : Function class
            Any of the measurement functions (see above)        
        rng : str or float
            Measurement range, 'AUTO' by default, ignored for diode, continuity, frequency and temperature
        nplc : float
            Number of power line cycles per measurement (not for 34450A)
        resolution : float
            Measurement resolution (34450A)
        samples : int
            Number of samples
        trigger_source : Trigger
            Sets the trigger source (IMMEDIATE by default)
        trigger_delay : float
            Sets the trigger delay (34465A and 34470A only)
        trigger_slop : bool
            Sets the trigger slope (True for positive, False for negative)
        sample_period : float
            Sets the sampling interval (34465A and 34470A only)
        """

        assert isinstance(function, Function), f"Invalid function type : {type(function)}"
        # Configure the function
        #self._prot.write(f'SENS:FUNC "{function.value}"')
        self._prot.write(f'CONF:{function.value}')

        # Set range
        if RANGES[function] is not None:
            assert rng in RANGES[function], f"Invalid range : {rng}"
            if function == Function.CURRENT_DC or function == Function.CURRENT_AC:
                if self._model in [Model._34461A, Model._34465A, Model._34470A]:
                    # The terminals have to be specified manually
                    if rng == 10:
                        # Activate 10A terminals
                        self._prot.write(f'SENS:{function.value}:TERM 10')
                    else:
                        # Activate 3A terminals
                        self._prot.write(f'SENS:{function.value}:TERM 3')
                        self._prot.write(f'SENS:{function.value}:RANG {rng}')
                else:
                    # The terminals are choosen automatically
                    self._prot.write(f'SENS:{function.value}:RANG {rng}')
            else:
                self._prot.write(f'SENS:{function.value}:RANG {rng}')

        if self._model == Model._34450A:
            if resolution is not None:
                # Resolution
                assert isinstance(resolution, float), f"Invalid resolution type : {type(resolution)}"
                self._prot.write(f'{function.value}:RES {nplc:.0f}')
        else:
            # NPLC
            assert nplc in NPLC_RANGES, f"Invalid NPLC value : {nplc}"
            self._prot.write(f'SENS:{function.value}:NPLC {nplc:.0f}')
        
        # Set samples count
        assert_number(samples)
        self._prot.write(f'SAMP:COUN {samples:.0f}')

        # Set trigger source
        assert isinstance(trigger_source, Trigger), f"Invalid trigger_source type : {type(trigger_source)}"
        self._prot.write(f'TRIG:SOUR {trigger_source.value}')

        # Set trigger delay
        if trigger_delay is not None:
            assert_number(trigger_delay)
            self._prot.write(f'TRIG:DEL {trigger_delay}')
        
        # Set trigger slope
        if trigger_slope is not None:
            self._prot.write(f'TRIG:SLOP {"POS" if trigger_slope else "NEG"}')
        
        if self._model in [Model._34465A, Model._34470A]:
            # Set sampling rate
            if sample_period is None:
                # Set sampling rate to immediate (default)
                self._prot.write('SAMP:SOUR IMM')
            else:
                self._prot.write('SAMP:SOUR TIM')
                assert_number(sample_period)
                self._prot.write(f'SAMP:TIM {sample_period:e}')