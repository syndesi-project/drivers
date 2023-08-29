from syndesi.adapters import IP, VISA
from syndesi.protocols.scpi import SCPI


SENSE_FUNCTIONS = ['voltage', 'current', 'resistance']
SOURCE_FUNCTIONS = ['voltage', 'current']

AUTO_KEYWORD = 'AUTO'



class Keithley2450():
    def __init__(self, adapter: IP) -> None:
        """
        Keithley 2450 SourceMeter unit

        Parameters
        ----------
        adpater : IAdapter
        """
        super().__init__()

        assert isinstance(adapter, IP) or isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter, end='\n')


    def set_output_state(self, state : bool):
        """
        Set the output state

        Parameters
        ----------
        state : bool
        """
        self._prot.write(f':OUTP {"ON" if state else "OFF"}')

    def set_source_function(self, function : str):
        """
        Set the source function : voltage or current

        Parameters
        ----------
        function : str
        """
        assert function in SOURCE_FUNCTIONS, f"Invalid function : {function}"
        self._prot.write(f':SOUR:FUNC {function}')

    def get_source_function(self) -> str:
        """
        Get the current source function

        Returns
        -------
        function : str
        """
        output = self._prot.query(':SOUR:FUNC?')
        functions_match = {
            'CURR' : 'current',
            'VOLT' : 'volt'
        }
        # Make it uppercase to avoid false detections
        output = output.upper()
        if output in functions_match:
            return functions_match[output]


    def set_measurement_function(self, function : str):
        """
        Set the measurement function : voltage, current or resistance

        Parameters
        ----------
        function : str
        """
        assert function in SENSE_FUNCTIONS, f"Invalid sense function : {function}"
        self._prot.write(f'FUNC "{function}"')

    def set_read_back_state(self, state : bool):
        """
        Enables or disables read back

            Disabled : The source value returned is the set source value (setpoint)
            Enabled : The source value returned is the measured value

        Parameters
        ----------
        state : bool
        """
        source_function = self.get_source_function()
        self._prot.write(f':SOUR:{source_function}:READ:BACK {"ON" if state else "OFF"}')


    def set_current_source_amplitude(self, current, max_voltage=None):
        """
        Sets the current source amplitude

        Range : -1.05A to +1.05A

        If max_voltage is specified, the maximum current will be set

        Parameters
        ----------
        current : float
        max_voltage : float
        """
        if max_voltage is not None:
            assert isinstance(max_voltage, float) or isinstance(max_voltage, int), f"Invalid max_voltage type : {type(max_voltage)}"
            self._prot.write(f':SOUR:CURR:VLIM {max_voltage}')
        assert isinstance(current, float) or isinstance(current, int), f"Invalid current type : {type(current)}"
        self._prot.write(f':SOUR:CURR {current}')

    def set_current_sense_range(self, rng):
        """
        Sets the current sensing range

        Any floating point value can be used, the instrument will
        determine automatically the appropriate range

        'AUTO' will put the device in auto mode

        Parameters
        ----------
        rng : float or str    
        """
        if isinstance(rng, str):
            if rng.upper() == AUTO_KEYWORD.upper():
                # Set in auto mode
                self._prot.write(':CURR:RANG:AUTO ON')
        elif isinstance(rng, float) or isinstance(rng, int):
            self._prot.write(f':CURR:RANG {rng}')
        else:
            raise ValueError(f"Invalid rng type : {type(rng)}")
        

    def set_voltage_sense_range(self, rng):
        """
        Sets the voltage sensing range

        Any floating point value can be used, the instrument will
        determine automatically the appropriate range

        'AUTO' will put the device in auto mode

        Parameters
        ----------
        rng : float or str
        """
        if isinstance(rng, str):
            if rng.upper() == AUTO_KEYWORD.upper():
                # Set in auto mode
                self._prot.write(':VOLT:RANG:AUTO ON')
        elif isinstance(rng, float) or isinstance(rng, int):
            self._prot.write(f':VOLT:RANG {rng}')
        else:
            raise ValueError(f"Invalid rng type : {type(rng)}")

    def set_voltage_source_amplitude(self, voltage, max_current=None):
        """
        Sets the voltage source amplitude

        Range : -210V to +210V

        If max_current is specified, the maximum current will be set

        Parameters
        ----------
        voltage : float
        max_current : float
        """
        if max_current is not None:
            assert isinstance(max_current, float) or isinstance(max_current, int), f"Invalid max_current type : {type(max_current)}"
            self._prot.write(f':SOUR:VOLT:ILIM {max_current}')
        assert isinstance(voltage, float) or isinstance(voltage, int), f"Invalid voltage type : {type(voltage)}"
        self._prot.write(f':SOUR:VOLT {voltage}')

    def set_front_terminals(self, enable : bool):
        """
        Enable or disables front/rear connectors

        Parameters
        ----------
        enable : bool
            True : Front terminals
            False : Rear terminals        
        """
        assert isinstance(enable, bool), f"Invalid enable type : {type(enable)}"
        self._prot.write(f':ROUT:TERM {"FRON" if enable else "REAR"}')

    def get_measurement(self, function) -> float:
        """
        Get a single measurement from the specified function : voltage,
        current or resistance

        Parameters
        ----------
        function : str
        """
        assert function in SENSE_FUNCTIONS, f"Invalid function : {function}"
        return float(self._prot.query(f':MEAS:{function}?'))
        
    def set_current_source_range(self, rng):
        """
        Sets the current source range

        Any floating point value can be used, the instrument will
        determine automatically the appropriate range

        Fixed current source ranges are :
        10nA, 100nA, 1uA, 10uA, 100uA, 1mA, 10mA, 100mA, 1A

        'AUTO' will put the device in auto mode

        Parameters
        ----------
        rng : float or str
        """
        if isinstance(rng, str):
            if rng.upper() == AUTO_KEYWORD.upper():
                # Set in auto mode
                self._prot.write('SOUR:CURR:RANG:AUTO ON')
        elif isinstance(rng, float) or isinstance(rng, int):
            self._prot.write(f'SOUR:CURR:RANG {rng}')
        else:
            raise ValueError(f"Invalid rng type : {type(rng)}")
        
    def set_voltage_source_range(self, rng):
        """
        Sets the voltage source range

        Any floating point value can be used, the instrument will
        determine automatically the appropriate range

        Fixed voltage source ranges are :
        20mV, 200mV, 2V, 20V, 200V

        'AUTO' will put the device in auto mode


        Parameters
        ----------
        rng : float or str
        """
        if isinstance(rng, str):
            if rng.upper() == AUTO_KEYWORD.upper():
                # Set in auto mode
                self._prot.write('SOUR:VOLT:RANG:AUTO ON')
        elif isinstance(rng, float) or isinstance(rng, int):
            self._prot.write(f'SOUR:VOLT:RANG {rng}')
        else:
            raise ValueError(f"Invalid rng type : {type(rng)}")
