from . import IAmmeter, IVoltmeter
from ..scpi_driver import SCPIDriver
from syndesi.adapters import Adapter, IP, VISA
from syndesi.protocols import SCPI
from enum import Enum
from typing import Union

# https://int.siglent.com/upload_file/user/SDM3055/SDM3055_RemoteManual_RC06035-E01A.pdf

__RANGE_TOLERANCE = 0.01 # 1%

class Range(Enum):
    def __init__(self, value) -> None:
        for x in dir(self):
            if x.startswith('_'):
                _range = getattr(self, x)
                if isinstance(_range, float) or isinstance(_range, int):
                    if _range * (1-__RANGE_TOLERANCE) <= value <= _range * (1+__RANGE_TOLERANCE):
                        return _range      

class ScannerCard(IVoltmeter, IAmmeter):
    class Function(Enum):
        VOLTAGE = 'DCV'
        VOLTAGE_AC = 'ACV'
        CURRENT = 'DCI'
        CURRENT_AC = 'ACI'
        RESISTANCE = '2W'
        RESISTANCE4 = '4W'
        CAPACITANCE = 'CAP'
        FREQUENCY = 'FRQ'
        CONTINUITY = 'CONT'
        DIODE = 'DIO'
        TEMPERATURE = 'TEMP'

    class VoltageRange(Range):
        _200mV = '200MLV' # TODO : Check this
        _2V = '2V'
        _20V = '20V'
        _200V = '200V'
        AUTO = 'AUTO'
    
    class CurrentRange(Range):
        _2A = '2A'
    
    class CurrentAcRange(Range):
        pass

    class VoltageAcRange(Range):
        pass

    class FrequencyRange(Range):
        pass

    class ResistanceRange(Range):
        _200 = '200OHM'
        _2k = '2KOHM'
        _20k = '20KOHM'
        _200k = '200KOHM'
        _2M = '2MOHM' # TODO : Check this
        _10M = '10MOHM'
        _100M = '100MOHM'
        AUTO = 'AUTO'
    
    class Resistance4Range(Range):
        pass

    class CapacitanceRange(Range):
        _2nF = '2NF'
        _20nF = '20NF'
        _200nF = '200NF'
        _2uF = '2UF'
        _20uF = '20UF'
        _200uF = '200UF'
        _10mF = '10000UF'
        AUTO = 'AUTO'

    class Speed(Range):
        SLOW = 'SLOW'
        FAST = 'FAST'

    class Impedance(Range):
        _10M = '10M'
        _10G = '10G'

    class TemperatureTransducer(Range):
        RTD_PT100 = 'RTD,PT100'
        RTD_PT1000 = 'RTD,PT1000'
        THER_BITS90 = 'THER,BITS90'
        THER_EITS90 = 'THER,EITS90'
        THER_JITS90 = 'THER,JITS90'
        THER_KITS90 = 'THER,KITS90'
        THER_NITS90 = 'THER,NITS90'
        THER_RITS90 = 'THER,RITS90'
        THER_SITS90 = 'THER,SITS90'
        THER_TITS90 = 'THER,TITS90'

    class Aperture(Range):
        _0_001 = '0.001'
        _0_01 = '0.01'
        _0_1 = '0.1'
        _1 = '1'

    def __init__(self, protocol : SCPI) -> None:
        super().__init__()
        self._prot = protocol

    
    def is_installed(self):
        """
        Return True if the scanner card is installed, return False otherwise

        Returns
        -------
        installed : bool
        """
        return bool(int(self._prot.query('ROUT:STAT?')))

    def set_status(self, enabled : bool):
        """
        Enable or disable the scanner card

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'ROUT:SCAN {"ON" if enabled else "OFF"}')

    def set_start(self, start : bool):
        """
        Start or stop scanning card measurement

        Parameters
        ----------
        start : bool
        """
        self._prot.write(f'ROUT:STAR {"ON" if start else "OFF"}')

    def set__loop_mode(self, mode : str):
        """
        Configure scan card loop mode (scan or step)

        Parameters
        ----------
        mode : str
            'scan' or 'step'
        """
        self._prot.write(f'ROUT:FUNC {mode}')

    def set__delay(self, delay : float):
        """
        Configure scanner card delay

        Parameters
        ----------
        delay : float
            Delay in seconds
        """
        self._prot.write(f'ROUT:DEL {delay}')
    
    def set_cycle_count(self, count : Union[int, str]):
        """
        Set the number of scanning card cycle measurements

        Parameters
        ----------
        count : int or str
            integer or 'AUTO'
        """
        if isinstance(count, str) and count.lower() == 'auto':
            self._prot.write('ROUT:COUN:AUTO ON')
        else:
            self._prot.write(f'ROUT:COUN {count}')

    def set_function(self, channel : int, switch : bool, function : Function, range : Range, speed : Speed, autozero : bool = None, aperture : Aperture = None):
        """
        Configure scanner card channel parameters

        Parameters
        ----------
        channel : int
            1 to 15
        switch : bool
            Enable or disable the channel
        mode : ScannerCardFunction
            Function
        range : ScannerCardRange
        speed : Speed
        autozero : bool
            Auto-zero for DC voltage and current measurements
        aperture : Aperture
            Gate time for frequency / period measurements
        """
        self._prot.write(f'ROUT:CHAN {channel},{"ON" if switch else "OFF"},{function.value},{range.value},{speed.value}')
        if autozero is not None:
            self._prot.write(f'ROUT:{function.value}:AZ {"ON" if autozero else "OFF"}')
        if aperture is not None:
            aperture = self.Aperture(aperture)
            self._prot.write(f'ROUT:{function.value}:APER {aperture.value}')
        

    def set_limits(self, lower = None, upper = None):
        """
        Sets the upper and lower limits of the scanning card channel

        Parameters
        ----------
        lower : int
            1 to 15
        upper : int
            1 to 15
        """
        if lower is not None:
            self._prot.write(f'ROUT:LIM:LOW {lower}')
        if upper is not None:
            self._prot.write(f'ROUT:LIM:HIGH {upper}')

    def get_last_measurement(self, channel : int):
        """
        Return the final measurement value of the scan card channel

        Parameters
        ----------
        channel : int
            1 to 15
        """
        value = float(self._prot.query(f'ROUT:DATA? {channel}'))
        return value

    def set_relative_mode(self, function : Function, relative : bool):
        """
        Configure the relative value switch of the scanner card measurement function

        Parameters
        ----------
        function : Function
        relative : bool
        """
        self._prot.write(f'ROUT:RELA {function.value},{"ON" if relative else "OFF"}')

    def set_impedance(self, impedance : Impedance):
        """
        Set input impedance of the scanner card

        Parameters
        ----------
        impedance : Impedance
        """
        self._prot.write(f'ROUT:IMP {impedance.value}')

    def set_temperature_transducer(self, transducer : TemperatureTransducer):
        """
        Configure thermal resistance model

        Parameters
        ----------
        transducer : TemperatureTransducer
        """
        self._prot.write(f'ROUT:TEMP:{transducer.value}')

    def set_temperature_unit(self, unit : str):
        """
        Set temperature unit

        Parameters
        ----------
        unit : str
            'C', 'F' or 'K'
        """
        self._prot.write(f'ROUT:TEMP:UNIT {unit.upper()}')

    def set_frequency_display_mode(self, period : bool):
        """
        Set frequency or period display mode

        Parameters
        ----------
        period : bool
            True : Period mode
            False : Frequency mode
        """
        self._prot.write(f'ROUT:{"FREQ" if period else "PER"}')

        




class SDM30x5(IVoltmeter, IAmmeter, SCPIDriver):
    AUTO_RANGE = 'AUTO'

    class Function(Enum):
        VOLTAGE = 'VOLT'
        VOLTAGE_AC = 'VOLT:AC'
        CURRENT = 'CURR'
        CURRENT_AC = 'CURR:AC'
        CONTINUITY = 'CONT'
        DIODE = 'DIOD'
        FREQUENCY = 'FREQ'
        PERIOD = 'PER'
        RESISTANCE4 = 'FRES'
        RESISTANCE = 'RES'
        CAPACITANCE = 'CAP'
        TEMPERATURE = 'TEMP'

    # Temperature types are common to all SDM30x5 multimeters as well as the scanner card
    TemperatureTransducer = ScannerCard.TemperatureTransducer

    class Impedance(Range):
        _10M = '10M'
        _10G = '10G'

    class Volume(Range):
        LOW = 'LOW'
        MIDDLE = 'MIDDLE'
        HIGH = 'HIGH'

    def __init__(self, adapter : Adapter) -> None:
        """
        Siglent SDM3055 5½ digit multimeter

        Parameters
        ----------
        adpater : Adapter
            Adapter to use, both IP and VISA are allowed
        """
        super().__init__(adapter)
        self._ranges = {}
        self._model = None

        assert isinstance(adapter, IP) or isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter)

    def test(self) -> bool:
        """
        Test if the instrument is up and running

        Returns
        -------
        success : bool
        """
        return self._model in self.get_identification() 

    def abort(self):
        """
        Aborts a measurement in progress, returning the instrument to the trigger idle state.
        """
        self._prot.write('ABOR')

    def get_values(self, clear_reading_memory=True, max_readings=None):
        """
        Waits for measurements to complete and returns all measurements currently in the reading memory
        
        Parameters
        ----------
        clear_reading_memory : bool
        """

        if clear_reading_memory:
            if max_readings is None:
                values = self._prot.write(f'READ?')
            else:
                values = self._prot.write(f'READ? {max_readings}')
        else:
            if max_readings is not None:
                raise ValueError("max_readings cannot be used when clear_reading_memory is False")
            values = self._prot.write('FETC?')

        return [float(x) for x in values.split(',') if x]

    def init(self):
        """
        Set the trigger state for “wait for trigger”. Measurements will begin when the specified trigger conditions are
        satisfied following the receipt of the init call. This method clears the instrument's reading memory
        """
        # TODO : Check if "IMM" is necessary here
        self._prot.write('INIT')

    def set_output_trigger_slope(self, positive : bool):
        """
        Selects the slope of the multimeter complete output signal on the rear-panel VM Comp BNC connector.
        
        Parameters
        ----------
        positive : bool
            True for positive, False for negative
        """
        self._prot.write(f'OUTP:TRIG:SLOP {"POS" if positive else "NEG"}')


    def set_sample_count(self, count : int):
        """
        Specifies the number of measurements (samples) the instrument will take per trigger.

        If a trigger count is set, the total number of returned measurement will be the
        product of the sample count and the trigger count

        10'000 readings can be stored in the instrument's memory. If the memory is full, oldest measurements will be overwritten

        Parameters
        ----------
        count : int
            Value from 1 to 599999999
        """
        self._prot.write(f'SAMP:COUN {count}')

    def set_temperature_unit(self, unit : str):
        """
        Selects the units (°C, °F, or Kelvin) to be used for all temperature measurements.

        Parameters
        ----------
        unit : str
            'C' (celsius), 'F' (fahrenheit) or 'K' (kelvin) 
        """
        self._prot.write(f'UNIT:TEMP {unit}')

    def clear_calculations(self):
        """
        Clears all limits, histogram data, statistics, and measurements
        """
        self._prot.write('CALC:CLE')

    def clear_limit_results(self):
        """
        Clear all Limit test results (Low Failures, High Failures, and Status), but do not clear the setting conditions
        of the Low Limit and High Limit.
        """
        self._prot.write('CALC:LIM:CLE')

    def set_limits(self, lower=None, upper=None):
        """
        Sets upper limit, lower limit or both

        Parameters
        ----------
        lower : float
        upper : float
        """
        if lower is not None:
            self._prot.write(f'CALC:LIM:LOW {lower}')
        if upper is not None:
            self._prot.write(f'CALC:LIM:UPP {upper}')

    def get_limits(self):
        """
        Return lower and upper limits

        Returns
        -------
        lower : float
        upper : float
        """
        lower = float(self._prot.query('CLAC:LIM:LOW?'))
        upper = float(self._prot.query('CLAC:LIM:UPP?'))

        return lower, upper

    def set_limits_state(self, enabled : bool):
        """
        Enable or disable limit testing

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'CALC:LIM {"ON" if enabled else "OFF"}')
    
    def get_limits_state(self):
        """
        Returns the state of limits testing

        Returns
        -------
        enabled : bool
        """
        _int = int(self._prot.query('CALC:LIM?'))
        return bool(_int)

    def get_histogram(self):
        """
        Return lower and upper histogram ranges, the number of measurements and the bin data collected since the last time the histogram data was cleared

        lower : float
            Lower range
        upper : float
            Upper range
        N : int
            Number of measurements
        below : int
            Number of measurements below the lower range
        bins : [int]
            Number of measurements in each bin
        above : int
            Number of measurements above the upper range
        """
        # NOTE : The ':DATA?' form was ommitted because it isn't necessary

        data_raw = self._prot.query('CALC:TRAN:HIST:ALL?')
        values = data_raw.split(',')
        lower = float(values[0])
        upper = float(values[1])
        N = int(values[2])
        below = int(values[3])
        bins = [int(x) for x in values[4:-1]]
        above = int(values[-1])

        return lower, upper, N, below, bins, above

    def clear_histogram(self):
        """
        Clears the histogram data and restarts histogram ranging only if histogram automatic range selection is enabled (with set_histrogram_range_mode)

        This method does not clear measurements in reading memory
        
        To clear statistics, limits, histogram data, and measurement data, use clear_calculations
        """
        self._prot.write('CALC:TRAN:HIST:CLE')

    def get_histogram_measurements(self):
        """
        Returns the number of measurements collected since the last time the histogram was cleared.

        Returns
        -------
        N : int
        """
        return int(self._prot.query('CALC:TRAN:HIST:COUN?'))
    
    def set_histogram_bins(self, N : int):
        """
        Sets the number of bins between the lower and upper range values for the histogram. Two additional bins always exist one for measurements below the lower range and one for measurements above the upper range.
        
        Parameters
        ----------
        N : int
        """
        self._prot.write(f'CALC:TRAN:HIST:POIN {N}')

    def set_histrogram_range(self, auto=False, lower=None, upper=None):
        """
        Set histogram ranging mode (automatic or manual) using auto=True or by setting lower and/or upper values

        Parameters
        ----------
        auto : bool
        lower : float
        upper : float
        """
        if auto:
            self._prot.write('CALC:TRAN:HIST:RANG:AUTO ON')
        else:
            if lower is not None:
                self._prot.write(f'CALC:TRAN:HIST:RANG:LOW {lower}')
            if upper is not None:
                self._prot.write(f'CALC:TRAN:HIST:RANG:UPP {upper}')

    def set_histogram_state(self, enabled : bool):
        """
        Enables or disables histogram computation

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'CALC:TRAN:HIST {"ON" if enabled else "OFF"}')

    def set_db_reference(self, reference_db : float):
        """
        Stores a relative value in the multimeter's dB Relative Register.
        When the dB function is enabled, this value will be subtracted from each
        voltage measurement after the measurement is converted to dBm.
        
        Parameters
        ----------
        reference_db : float or str
            value or 'auto' to use the first measurement as reference
        """
        if isinstance(reference_db, str) and reference_db.lower() == 'auto':
            self._prot.write('CALC:SCAL:REF:AUTO ON')
        else:
            self._prot.write(f'CALC:SCAL:DB:REF {reference_db}')

    def set_dbm_reference(self, reference : float):
        """
        Selects the reference resistance for converting voltage measurements to dBm. This reference value affects the dBm and dB scaling functions.

        Parameters
        ----------
        reference : float
        """
        self._prot.write(f'CALC:SCAL:DBM:REF {reference}')

    def set_scaling(self, enabled : bool, mode : str):
        """
        enable/disable and select the operation performed by the scaling function

        Parameters
        ----------
        enabled : bool

        mode : str
            'db' or 'dbm' 
        """
        self._prot.write(f'CALC:SCAL {"ON" if enabled else "OFF"}')
        self._prot.write(f'CALC:SCAL:FUNC {mode}')

    def set_average_state(self, enabled : bool):
        """
        Enables or disables statistics computation

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'CALC:AVER {"ON" if enabled else "OFF"}')

    def get_average_statistics(self):
        """
        Return arithmetric mean (average), standard deviation, number of measurements and min/max values

        Returns
        -------
        mean : float
        std : float
        count : int
        _min : float
        _max : float
        """
        output = self._prot.query('CALC:AVER:ALL?')
        count = int(self._prot.query('CALC:AVER:COUN?'))
        mean, std, _min, _max = [float(x) for x in output.split(',') if x]
        return mean, std, count, _min, _max

    def clear_average(self):
        """
        Clears all computed statistics: minimum, maximum, average, peak-to-peak, count and standard deviation
        """
        self._prot.write('CALC:AVER:CLE')

    def get_function(self):
        """
        Return function and range

        Returns
        -------
        function : Function
        range : float
        """
        output = self._prot.query('CONF?')
        values = output.strip(' ').split(',')
        function = self.Function(values[0])
        if len(values) > 1:
            # There is a range
            _range = self._ranges[function](values[1])
        else:
            _range = None

        return function, _range

    def set_function(self,
            function : Union[str, Function],
            _range : Range = AUTO_RANGE,
            null_function_enabled = None,
            null_value : Union[float, str] = None,
            nplc : Range = None,
            bandwidth : Range = None,
            autozero : bool = None,
            filter : bool = None,
            aperture : Range = None,
            impedance : Impedance = None,
            threshold : float = None,
            volume : Volume = None):
            
        """
        Set measurement function of the instrument

        Parameters
        ----------
        function : str or Function
        _range : Range
            AUTO by default
        null_function_enabled : bool
            Enable or disable null function
        null_value : float or str
            Null value, set to 'AUTO' for automatic mode
        nplc : self.NPLC
            Number of powerline cycles for one measurement
        bandwidth : self.Bandwidth
            Sets the bandwidth for AC measurements (SDM3065X only)
        autozero : bool
            Auto-zero for DC measurements
        filter : bool
            Filter for DC current measurements (only for SDM3045X and SDM3055)
        aperture : Aperture
            Set gate time for frequency and period measurements (SDM3065X only)
        impedance : Impedance
            Select input impedance of DC voltage measurement. Suitable only for the following
            device and range combinations :
            - SDM3045X : 600mV
            - SDM3055  : 200mV and 2V
            - SDM3065X : 200mV, 2V and 20V 
        threshold : float
            Continuity threshold between 0 and 2000 (default 50)
        value : Volume
            Continuity volume
        """
        # Set function and range
        function = self.Function(function)
        if function in self._ranges:
            # If a range exist, send a command with a range
            self._prot.write(f'CONF:{function.value} {_range.value}')
        else:
            # Otherwise, send conf only
            self._prot.write(f'CONF:{function.value}')
        # Set null function
        if null_function_enabled is not None:
            self._prot.write(f'{function.value}:NULL {"ON" if null_function_enabled else "OFF"}')
        if null_value is not None:
            if isinstance(null_value, str) and null_value.upper == 'auto':
                self._prot.write(f'{function.value}:NULL:VALUE:AUTO ON')
            else:    
                self._prot.write(f'{function.value}:NULL:VALUE {null_value}')
        # NPLC
        if nplc is not None:
            self._prot.write(f'{function.value}:NPLC {nplc.value}')
        # Bandwidth
        if bandwidth is not None:
            self._prot.write(f'{function.value}:BAND {bandwidth.value}')
        # Auto-zero
        if autozero is not None:
            self._prot.write(f'{function.value}:AZ {"ON" if autozero else "OFF"}')
        # Filter
        if filter is not None:
            self._prot.write(f'{function.value}:FILT {"ON" if filter else "OFF"}')
        # Aperture
        if aperture is not None:
            self._prot.write(f'{function.value}:APER {aperture.value}')
        # Impedance
        if impedance is not None:
            self._prot.write(f'{function.value}:IMP {impedance.value}')
        if threshold is not None:
            self._prot.write(f'{function.value}:THR:VAL {threshold}')
        if volume is not None:
            self._prot.write(f'{function.value}:VOL:STAT {volume.value}')



    def get_last_measurement(self):
        """
        Return the last measurement taken. Can be called at anytime

        Returns
        -------
        value : float
        """
        return float(self._prot.query('DATA:LAST?'))

    def get_reading_count(self):
        """
        Return the total number of measurements currently in reading memory. Can be called at anytime

        Returns
        -------
        count : int
        """
        return int(self._prot.query('DATA:POIN?'))

    # def get_(self, N : int):
    #     """
    #     Read and erase N measurements from reading memory (oldest first)

    #     Parameters
    #     ----------
    #     N : int

    #     Returns
    #     -------
    #     values : [float]
    #     """
    #     values_raw = self._prot.query(f'DATA:REM? {N}')
    #     return [float(x) for x in values_raw.split(',') if x]
    # TODO : Check if DATA:REM? / R? / READ? don't do all the same, if it is the case, this function can be removed

    

    # TODO : Implement measure subsystem



    def measure_continuity(self) -> bool:
        """
        Make a continuity measurement and return True is the circuit is closed. Range is fixed at 2kΩ
        
        Returns
        -------
        continuity : bool
            True if closed, False if open
        """
        THRESHOLD = 2e3
        value = float(self._prot.query('MEAS:CONT?'))
        return value < THRESHOLD

    def measure_ac_current(self) -> float:
        """
        Make an AC current measurement and return the result

        Returns
        -------
        current : float
        """
        output = float(self._prot.query('MEAS:CURR:AC?'))
        return output

    def measure_dc_current(self) -> float:
        """
        Make a DC current measurement and return the result

        Returns
        -------
        current : float
        """
        output = float(self._prot.query('MEAS:CURR:DC?'))
        return output

    def measure_diode(self) -> Union[float, None]:
        """
        Make a diode measurement (voltage). The range is fixed at 2VDC, if the measured
        value is higher, None is returned. Otherwise, the diode voltage is returned
        
        Returns
        -------
        voltage : float
        """
        THRESHOLD = 2
        voltage = float(self._prot.query('MEAS:DIOD?'))
        if voltage > THRESHOLD:
            return None
        else:
            return voltage

    def measure_frequency(self) -> float:
        """
        Make a frequency measurement

        Returns
        -------
        frequency : float
        """
        return float(self._prot.query('MEAS:FREQ?'))

    def measure_frequency(self) -> float:
        """
        Make a period measurement

        Returns
        -------
        period : float
        """
        return float(self._prot.query('MEAS:PER?'))

    def measure_resistance(self, four_wire = False) -> float:
        """
        Make a resistance measurement

        Parameters
        ----------
        four_wire : bool
    
        Returns
        -------
        resistance : float
        """
        if four_wire:
            return float(self._prot.query('MEAS:FRES?'))
        else:
            return float(self._prot.query('MEAS:RES?'))


    def measure_temperature(self, type : TemperatureTransducer) -> float:
        """
        Make a temperature measurement

        Parameters
        ----------
        type : TemperatureTransducer

        Returns
        -------
        temperature : float
        """
        return float(self._prot.query(f'MEAS:TEMP? {type.value}'))

    def measure_ac_voltage(self) -> float:
        """
        Make an AC voltage measurement and return the result

        Returns
        -------
        voltage : float
        """
        output = float(self._prot.query('MEAS:VOLT:AC?'))
        return output

    def measure_dc_voltage(self) -> float:
        """
        Make a DC voltage measurement and return the result

        Returns
        -------
        voltage : float
        """
        output = float(self._prot.query('MEAS:VOLT:DC?'))
        return output

    def measure_capacitance(self) -> float:
        """
        Make a capacitance measurement

        Returns
        -------
        capacitance : float
        """
        return float(self._prot.query('MEAS:CAP?'))

    def set_beeper_state(self, enabled : bool):
        """
        Enable or disable the beeper during continuity, diode or probe hold measurements

        Parameters
        ----------
        enabled : bool
        """
        self._prot.write(f'SYST:BEEP:STAT {"ON" if enabled else "OFF"}')

    def system_preset(self):
        """
        This command is nearly identical to reset. The difference is that, for SCPI operations,
        reset restores the machine to factory default parameters, while system_preset restores the
        machine's parameter configuration to the state configuration when the power is up.
        """
        self._prot.write('SYST:PRES')

    def get_static_ip_address(self):
        """
        Return static ip address

        Returns
        -------
        ip : str
        """
        return self._prot.query('SYST:COMM:LAN:IPAD? STAT')

    def get_current_ip_address(self):
        """
        Return current ip address

        Returns
        -------
        ip : str
        """
        return self._prot.query('SYST:COMM:LAN:IPAD? CURR')

    def set_static_ip_address(self, ip : str):
        """
        Set static ip address

        Parameters
        ----------
        ip : str
        """
        self._prot.write(f'SYST:COMM:LAN:IPAD {ip}')

    def get_static_subnet_mask(self):
        """
        Return static subnet mask

        Returns
        -------
        mask : str
        """
        return self._prot.query('SYST:COMM:LAN:SMAS? STAT')

    def get_current_subnet_mask(self):
        """
        Return current subnet mask

        Returns
        -------
        mask : str
        """
        return self._prot.query('SYST:COMM:LAN:SMAS? CURR')

    def set_static_subnet_mask(self, mask : str):
        """
        Set static subnet mask

        Parameters
        ----------
        mask : str
        """
        self._prot.write(f'SYST:COMM:LAN:SMAS {mask}')

    def get_gpib_address(self):
        """
        Return GPIB address

        Returns
        -------
        address : int
        """
        return int(self._prot.query('SYST:COMM:GPIB:ADDR?'))
    
    def set_gpib_address(self, address : int):
        """
        Set GPIB address

        Parameters
        ----------
        address : int
        """
        self._prot.write(f'SYST:COMM:GPIB:ADDR {address}')
    
    def get_gateway(self):
        """
        Return gateway ip address
        
        Parameters
        ----------
        gateway : str
        """
        return self._prot.query('SYST:COMM:LAN:GAT?')

    def set_gateway(self, gateway : str):
        """
        Set default gateway ip
        
        Parameters
        ----------
        gateway : ip
        """
        self._prot.write(f'SYST:COMM:LAN:GAT {gateway}')

    def set_trigger_count(self, N : int):
        """
        Selects the number of triggers that are accepted by
        the instrument before returning to the idle trigger state

        Parameters
        ----------
        N : int
        """
        self._prot.write(f'TRIG:COUN {N}')
    
    def set_trigger_delay(self, delay : float):
        """
        Set the delay between the trigger signal and the first measurement to 
        make sure the input signal is stable until the measurement is made.
        
        Parameters
        ----------
        delay : float or str
            delay in seconds (1μs increments) 0.0 to 3600.0. 'AUTO' to enable automatic delay
        """
        if isinstance(delay, str) and delay.lower() == 'auto':
            self._prot.write('TRIG:DEL:AUTO ON')
        else:
            self._prot.write(f'TRIG:DEL {delay}')

    def set_trigger_slope(self, slope : str):
        """
        Set trigger slope (positive of negative)

        Parameters
        ----------
        slope : str
            'positive' or 'negative'
        """
        if slope.lower() == 'positive':
            argument = 'POS'
        elif slope.lower() == 'negative':
            argument = 'NEG'
        else:
            raise ValueError("Invalid slope value")
        
        self._prot.write(f'TRIG:SLOP {argument}')

    def set_trigger_source(self, source : str):
        """
        Set trigger source

            - immediate : The trigger signal is always present, when the instrument
            is placed in the "wait-for-trigger" state, the trigger is issued immeditately
            - bus : The instrument is triggered by trigger() over the remote interface
            once the DMM is in the wait-for-trigger state
            - external : The instrument accepts hardware triggers applied to
            the rear-panel Ext Trig input and takes the specified number of measurements
            (sample count), each time a TTL pulse specified by set_trigger_slope is received.
            If the instrument receives an external trigger before it is ready, it will buffer one trigger.
        
        Parameters
        ----------
        source : str
            'immediate', 'bus' or 'external'
        """
        values = {
            'immediate' : 'IMM',
            'bus' : 'BUS',
            'external' : 'EXT'
        }
        if source.lower() not in values:
            raise ValueError("Invalid source")
        
        self._prot.write(f'TRIG:SOUR {values[source.lower()]}')

    def scanner_card(self) -> ScannerCard:
        return ScannerCard(self._prot)    

class SDM3045X(SDM30x5):
    class VoltageRange(Range):
        _600mV = '600mV'
        _6V = '6V'
        _60V = '60V'
        _600V = '600V'
        _1000V = '1e3V'
        AUTO = SDM30x5.AUTO_RANGE
    
    class VoltageRangeAC(Range):
        _600mV = '600mV'
        _6V = '6V'
        _60V = '60V'
        _600V = '600V'
        _750V = '750V'
        AUTO = SDM30x5.AUTO_RANGE

    class CurrentRange(Range):
        _600uA = '600uA'
        _6mA = '6mA'
        _60mA = '60mA'
        _600mA = '600mA'
        _6A = '6A'
        _10A = '10A'
        AUTO = SDM30x5.AUTO_RANGE
    
    class CurrentRangeAC(Range):
        _60mA = '60mA'
        _600mA = '600mA'
        _6A = '6A'
        _10A = '10A'
        AUTO = SDM30x5.AUTO_RANGE

    class ResistanceRange(Range):
        _600 = '600'
        _6k = '6k'
        _60k = '60k'
        _600k = '600k'
        _6M = '6M'
        _60M = '60M'
        _100M = '100M'
        AUTO = SDM30x5.AUTO_RANGE

    class CapacitanceRange(Range):
        _2nF = '2nF'
        _20nF = '20nF'
        _200nF = '200nF'
        _2uF = '2uF'
        _20uF = '20uF'
        _200uF = '200uF'
        _10mF = '10000uF'
        AUTO = SDM30x5.AUTO_RANGE

    class NPLC(Range):
        FAST = '0.3'
        MIDDLE = '1'
        SLOW = '10'


    def __init__(self, adapter: Adapter) -> None:
        super().__init__(adapter)
        self._model = 'SDM3045X'
        self._ranges = {
            self.Function.VOLTAGE : self.VoltageRange,
            self.Function.VOLTAGE_AC : self.VoltageRangeAC,
            self.Function.CURRENT : self.CurrentRange,
            self.Function.CURRENT_AC : self.CurrentRangeAC,
            self.Function.RESISTANCE : self.ResistanceRange,
            self.Function.RESISTANCE4 : self.ResistanceRange,
            self.Function.CAPACITANCE : self.CapacitanceRange,
            self.Function.TEMPERATURE : self.TemperatureTransducer
        }
        self._nplc = self.NPLC

class SDM3055(SDM30x5):
    class VoltageRange(Range):
        _200mV = '200mV'
        _2V = '2V'
        _20V = '20V'
        _200V = '200V'
        _1000V = '1000V'
        AUTO = SDM30x5.AUTO_RANGE
    
    class VoltageRangeAC(Range):
        _200mV = '200mV'
        _2V = '2V'
        _20V = '20V'
        _200V = '200V'
        _750V = '750V'
        AUTO = SDM30x5.AUTO_RANGE

    class CurrentRange(Range):
        _200uA = '200uA'
        _2mA = '2mA'
        _20mA = '20mA'
        _200mA = '200mA'
        _2A = '2A'
        _10A = '10A'
        AUTO = SDM30x5.AUTO_RANGE
    
    class CurrentRangeAC(Range):
        _20mA = '20mA'
        _200mA = '200mA'
        _2A = '2A'
        _10A = '10A'
        AUTO = SDM30x5.AUTO_RANGE

    class ResistanceRange(Range):
        _200 = '200'
        _2k = '2k'
        _20k = '20k'
        _200k = '200k'
        _2M = '2M'
        _10M = '10M'
        _100M = '100M'
        AUTO = SDM30x5.AUTO_RANGE

    class CapacitanceRange(Range):
        _2nF = '2nF'
        _20nF = '20nF'
        _200nF = '200nF'
        _2uF = '2uF'
        _20uF = '20uF'
        _200uF = '200uF'
        _10mF = '10000uF'
        AUTO = SDM30x5.AUTO_RANGE

    class NPLC(Range):
        FAST = '0.3'
        MIDDLE = '1'
        SLOW = '10'

    def __init__(self, adapter: Adapter) -> None:
        super().__init__(adapter)
        self._model = 'SDM3055'
        self._ranges = {
            self.Function.VOLTAGE : self.VoltageRange,
            self.Function.VOLTAGE_AC : self.VoltageRangeAC,
            self.Function.CURRENT : self.CurrentRange,
            self.Function.CURRENT_AC : self.CurrentRangeAC,
            self.Function.RESISTANCE : self.ResistanceRange,
            self.Function.RESISTANCE4 : self.ResistanceRange,
            self.Function.CAPACITANCE : self.CapacitanceRange
        }
        self._nplc = self.NPLC

class SDM3065X(SDM30x5):
    class VoltageRange(Range):
        _200mV = '200mV'
        _2V = '2V'
        _20V = '20V'
        _200V = '200V'
        _1000V = '1000V'
        AUTO = SDM30x5.AUTO_RANGE
    
    class VoltageRangeAC(Range):
        _200mV = '200mV'
        _2V = '2V'
        _20V = '20V'
        _200V = '200V'
        _750V = '750V'
        AUTO = SDM30x5.AUTO_RANGE

    class CurrentRange(Range):
        _200uA = '200uA'
        _2mA = '2mA'
        _20mA = '20mA'
        _200mA = '200mA'
        _2A = '2A'
        _10A = '10A'
        AUTO = SDM30x5.AUTO_RANGE
    
    class CurrentRangeAC(Range):
        _200uA = '200uA'
        _2mA = '2mA'
        _20mA = '20mA'
        _200mA = '200mA'
        _2A = '2A'
        _10A = '10A'
        AUTO = SDM30x5.AUTO_RANGE

    class ResistanceRange(Range):
        _200 = '200'
        _2k = '2k'
        _20k = '20k'
        _200k = '200k'
        _1M = '1M'
        _10M = '10M'
        _100M = '100M'
        AUTO = SDM30x5.AUTO_RANGE

    class CapacitanceRange(Range):
        _2nF = '2nF'
        _20nF = '20nF'
        _200nF = '200nF'
        _2uF = '2uF'
        _20uF = '20uF'
        _200uF = '200uF'
        _2mF = '2mF'
        _20mF = '20mF'
        _100mF = '100mF'
        AUTO = SDM30x5.AUTO_RANGE

    class NPLC(Range):
        _0005 = '0.005'
        _005 = '0.05'
        _05 = '0.5'
        _1 = '1'
        _10 = '10'
        _100 = '100'

    class Bandwidth(Range):
        _3Hz = '3Hz'
        _20Hz = '20Hz'
        _200Hz = '200Hz'

    def __init__(self, adapter: Adapter) -> None:
        super().__init__(adapter)
        self._model = 'SDM3065X'
        self._ranges = {
            self.Function.VOLTAGE : self.VoltageRange,
            self.Function.VOLTAGE_AC : self.VoltageRangeAC,
            self.Function.CURRENT : self.CurrentRange,
            self.Function.CURRENT_AC : self.CurrentRangeAC,
            self.Function.RESISTANCE : self.ResistanceRange,
            self.Function.RESISTANCE4 : self.ResistanceRange,
            self.Function.CAPACITANCE : self.CapacitanceRange
        }
        self._nplc = self.NPLC