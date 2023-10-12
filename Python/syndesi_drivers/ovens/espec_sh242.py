from syndesi.adapters import IP
from syndesi.protocols.delimited import Delimited
from datetime import datetime, date, time
from syndesi.tools.types import is_number, assert_number
import re

ERROR_PREFIX = 'NA:'

class SH242Exception(Exception):
    ERROR_CODES = {
    ERROR_PREFIX + 'CMD_ERR': 'Main command error, the command has probably been mistyped',
    ERROR_PREFIX + 'PARA ERR': 'Option parameter error, text was probably entered instead of numerical value',
    ERROR_PREFIX + 'DATA NOT READY': 'Specified data does not exist',
    ERROR_PREFIX + 'DATA OUT OF RANGE': 'Specified value outside the setting range',
    ERROR_PREFIX + 'PROTECT ON': 'Setting prohibited by network protection',
    ERROR_PREFIX + 'INVALID REQ': 'Unsupported function specified, this chamber does not have the necessary options',
    ERROR_PREFIX + 'CHB NOT READY': 'Command specified when the chamber is not ready to receive (invalid state)'
    }
    def __init__(self, code : bytearray) -> None:
        if code in self.ERROR_CODES:
            self.message = self.ERROR_CODES[code]
        else:
            self.message = f"Unknown error : {code}"
        super().__init__(self.message)

MAX_PROGRAM_NUMBER = 8
OFF_KEYWORD = 'OFF'

# Vocabulary
#
# "Exposure" (GRANTY ON or GRANTY OFF) is the "soak" time
#   - ON : time starts counting only when the desired setpoint is reached
#   - OFF : time starts counting immediately


class SH242():
    def __init__(self, adapter: IP) -> None:
        """
        ESPEC SH-242 driver

        by default the ESPEC uses TCP on port 57732

        Parameters
        ----------
        adapter : IP
            IP Adapter
        """
        super().__init__()
        assert isinstance(adapter, IP), "Invalid adapter"
        adapter.set_default_port(57732)
        self._prot = Delimited(adapter, termination='\r\n')


    def _query(self, data):
        """
        Write to the SH242

        Parameters
        ----------
        data : str
        """
        output = self._prot.query(data)
        if len(output) == 0:
            # If there's no output, it probably means that the SH242 is
            # busy with another client
            raise RuntimeError("No response from SH-242, another client is probably connected")
        elif output.startswith(ERROR_PREFIX):
            raise SH242Exception(output)
        else:
            return output

    def _get_internal_date(self) -> date:
        """
        Monitors the date of the internal calendar

        Returns
        -------
        date : date
            Date object containing year, month and day
        """
        output = self._query('DATE?')
        
        DATE_FORMAT = r'%y.%m/%d'
        _date = datetime.strptime(output.strip(), DATE_FORMAT)
        return date(_date.year, _date.month, _date.day)

    def _get_internal_time(self) -> time:
        """
        Monitors the time of the internal calendar

        Returns
        -------
        time : time
            Time object containing hour, minutes and seconds
        """
        output = self._query('TIME?')
        TIME_FORMAT = r'%H:%M:%S'
        _time = datetime.strptime(output.strip(), TIME_FORMAT)
        return time(_time.hour, _time.minute, _time.second)

    def get_internal_datetime(self) -> datetime:
        """
        Monitors the date and time of the internal calendar

        Returns
        -------
        datetime : datetime
        """
        return datetime.combine(self._get_internal_date(), self._get_internal_time())


    def get_current_running_program_number(self):
        """
        Returns the currently running program number, if no program is running, zero is returned

        Returns
        -------
        program_number : int
        """
        try:
            output = self._query('PRGM MON?')
        except SH242Exception:
            # There is an error, no program is running
            program_number = 0
        else:
            # There are multiple values, parse response as such :
            # program_number, step_number, temperature_setpoint[, humidity_setpoint], step_remaining_time, counter_a_remaining, counter_b_remaining
            # 1, 2, 27.0, 85, 0:58, 1, 2
            values = output.strip().split(',', maxsplit=1)
            program_number = int(values[0])            

        return program_number

    def get_running_program_information(self):
        """
        Returns the program area, program pattern name, and end setting of the program operation beign executed.

        End conditions :

            "OFF" : Power off the unit
            "STANDBY" : Disable regulation and keep the unit on
            "CONSTANT" : Enable constant regulation of temperature and humidity
            "HOLD" : Hold the last program values as regulation setpoints
            "RUN" : Run a program

        Returns
        -------
        program_number : int
            Pattern number during operation
        program_name : str
            Missing information on this
        end_condition : str
            Condition on end of the program (see above)
        """
        output = self._query('PRGM SET?')
        # Parse reponse : RAM:x, <program_name>, END(y)
        print(output)
        pattern = r'RAM:([0-9]+),\s*([^,]+),\s*END\((\w+)\)'
        groups = re.match(pattern, output)
        if groups is not None:
            return int(groups[1]), groups[2], groups[3]
        else:
            return 0, '', ''

    def get_available_program_numbers(self) -> list:
        """
        Return a list of available program numbers

        Output is empty if there are no programs

        Returns
        -------
        programs : list
        """
        output = self._query('PRGM USE?,RAM')
        # Parse response : N, 1, 2, 5, etc... (N the number of programs)
        return [int(x) for x in output.strip().split(',')][1:]

    def get_program_details(self, program: int):
        """
        Returns the details of the specified program as a dictionnary.
        If the program doesn't exist, an empty dictionnary is returned.
        If the program exists, the dictionnary contains :
            'steps' : The number of steps
            'name' : The name of the program
            'counter_A' : Counter A settings (see below)
            'counter_' : Counter B settings
            'end_condition' : End condition (see below)

        Counter settings in the form (X,Y,Z) :
                X : The step at which the counter jumps back
                Y : The step at which the counter starts
                Z : The number of cycles

        End condition : 
            "OFF" : Power off the unit
            "STANDBY" : Disable regulation and keep the unit on
            "CONSTANT" : Enable constant regulation of temperature and humidity
            "HOLD" : Hold the last program values as regulation setpoints
            "RUN" : Run a program

        Parameters
        ----------
        program : int
            Program number

        Returns
        -------
        values : dict
        """
        assert_number(program)
        output = self._query(f'PRGM DATA?,RAM:{program:d}')
        # Parse response : number_steps,<name>,COUNT,A(X.Y.Z),B(X.Y.Z),END(c)
        # 5,<PGM-1>,COUNT,A(1.3.10),B(0.0.0),END(OFF)
        pattern = r'([0-9]+),\s*<(\S+)>,\s*COUNT,\s*A\(([0-9]+).\s*([0-9]+).\s*([0-9]+)\),\s*B\(([0-9]+).\s*([0-9]+).\s*([0-9]+)\),\s*END\((\w+)\)'
        match = re.match(pattern, output)
        if match is not None:
            groups = match.groups()
            return {
                'steps' : int(groups[0]),  # number_steps
                'name': groups[1],
                'counter_A' : tuple([int(x) for x in groups[2:5]]),
                'counter_' : tuple([int(x) for x in groups[5:8]]),
                'end_condition' : groups[8]
            }
        else:
            return {}

    def get_program_step_information(self, program: int, step: int):
        """
        Return information of the specified step in the specified program

        Parameters
        ----------
        program : int
        step : int

        Returns
        -------
        temperature_setpoint : float
        temperature_ramp_enabled : bool
        humidity_setpoint : int
        humidity_ramp_enabled : bool
        time : int
            Number of minutes for this particular step
        soak_time : bool
            True : wait for the setpoint to be reached before counting time
            False : counting starts immediately
        refrigerator_setting : int
            See 'get_refrigerator_setpoint()'
        time_signal : tuple
            None if time signal is disabled, else the raw value (TODO : change this)
        pause_enabled : bool
        """
        assert_number(program)
        assert_number(step)
        output = self._query(f'PRGM DATA?,RAM:{program:d},STEP{step:d}')
        # TODO : check this
        time_signal_enabled = 'RELAY ON' in output or 'RELAY OFF' in output
        if time_signal_enabled:
            # Look for the time_setting info
            pattern = r'[0-9]+,\s*TEMP([\-0-9.]+),\s*TEMP RAMP ([\w]+),\s*HUMI([0-9]+),\s*HUMI RAMP (\w+),\s*TIME([0-9:]+),\s*GRANTY (\w+),\s*REF([0-9]),\s*RELAY ([\w.]+),\s*PAUSE (\w+)'
        else:
            # Do not look for it
            pattern = r'[0-9]+,\s*TEMP([\-0-9.]+),\s*TEMP RAMP ([\w]+),\s*HUMI([0-9]+),\s*HUMI RAMP (\w+),\s*TIME([0-9:]+),\s*GRANTY (\w+),\s*REF([0-9]),\s*PAUSE (\w+)'

        groups = re.match(pattern, output).groups()
        if not time_signal_enabled:
            # Insert a None value
            groups = groups[:7] + (None, ) + groups[7:]
        hours, minutes = [int(x) for x in groups[4].split(':')]
        return (float(groups[0]),  # temperature_setpoint
                groups[1] == 'ON',  # temperature_ramp_enabled
                int(groups[2]),  # humidity_setpoint
                groups[3] == 'ON',  # humidity_ramp_enabled
                hours * 60 + minutes,
                groups[5] == 'ON',  # soak_time
                int(groups[6]),  # refrigerator_setting
                groups[7],  # time_signal
                groups[8] == 'ON')  # pause_enabled

    def get_program_information_extra(self, program: int):
        """
        Return extra information about the specified program

        Start settings :
            OFF : Start value is disabled
            PV  : measured value
            SV  : Set value

        Parameters
        ----------
        program : int

        Returns
        -------
        temperature_warning_upper_limit : float
        temperature_warning_lower_limit : float
        humidity_warning_upper_limit : int
        humidity_warning_lower_limit : int
        temperature_start_setting : str
        temperature_start_value : float
        humidity_start_setting : str
        humidity_start_value : int
        """
        output = self._query(f'PRGM DATA?,RAM:{program},DETAIL')
        values = output.split(',')
        return (float(values[0]),  # temperature_warning_upper_limit
                float(values[1]),  # temperature_warning_lower_limit
                int(values[2]),  # humidity_warning_upper_limit
                int(values[3]),  # humidity_warning_lower_limit
                values[4].strip(' ')[4:],  # temperature_start_setting
                float(values[5]),  # temperature_start_value
                values[6].strip(' ')[4:],  # humidity_start_setting
                int(values[7]))  # humidity_start_value

    def get_temperature(self) -> float:
        """
        Return the current measured temperature inside the chamber

        Returns
        -------
        temperature : float
        """
        return self.get_temperature_parameters()[0]

    def get_temperature_parameters(self):
        """
        Returns current temperature parameters

        Returns
        -------
        measured_temperature : float
        temperature_setpoint : float or str
            'OFF' if disabled
        temperature_upper_limit_alarm_value : float
        temperature_lower_limit_alarm_value : float
        """
        # Parse response format :
        # measured_temperature, temperature_setpoint, temperature_upper_limit_alarm_value, temperature_lower_limit_alarm_value
        output = self._query('TEMP?')
        values = output.strip().split(',')
        temperature = float(values[0])
        try:
            setpoint = float(values[1])
        except ValueError:
            # 'OFF'
            setpoint = values[1]
        temperature_upper_limit_alarm_value = float(values[2])
        temperature_lower_limit_alarm_value = float(values[3])
        
        return (temperature, setpoint, temperature_upper_limit_alarm_value, temperature_lower_limit_alarm_value)

    def get_humidity(self) -> float:
        """
        Return the current measured relative humidity inside the chamber

        Returns
        -------
        humidity : int
        """
        return self.get_humidity_parameters()[0]

    def get_humidity_parameters(self):
        """
        Returns current humidity parameters

        Returns
        -------
        measured_humidity : int
        humidity_setpoint : int or str
            'OFF' if disabled
        humidity_upper_limit_alarm_value : int
        humidity_lower_limit_alarm_value : int
        """
        # Parse response format :
        # measured_humidity, humidity_setpoint, humidity_upper_limit_alarm_value, humidity_lower_limit_alarm_value
        output = self._query('HUMI?')
        values = output.strip().split(',')
        humidity = int(values[0])
        try:
            setpoint = int(values[1])
        except ValueError:
            # 'OFF'
            setpoint = values[1]
        humidity_upper_limit_alarm_value = int(values[2])
        humidity_lower_limit_alarm_value = int(values[3])
        

        return (humidity, setpoint, humidity_upper_limit_alarm_value, humidity_lower_limit_alarm_value)

    def get_operation_state(self, detailed=False):
        """
        Returns the chamber operation state

            Panel power off            : "OFF"
            All operation stop         : "STANDBY"
            Constant operation         : "CONSTANT"
            Program / remote operation : "RUN"

        If detailed is True, additionnal information is returned

            Panel power off            : "OFF"
            All operation stop         : "STANDBY"
            Constant operation         : "CONSTANT"
            Program operating          : "RUN"
            Program pausing            : "RUN PAUSE"
            Program operation end hold : "RUN END HOLD"
            Remote program operating   : "RMT RUN"
            Remote program pausing     : "RMT RUN PAUSE"
            Program operation end hold : "RMT RUN END HOLD"



        Parameters
        ----------
        detailed : bool
            Add detailed information (default to False)

        Returns
        -------
        operation_state : str
        """
        COMMAND = 'MODE?'
        if detailed:
            COMMAND += ',DETAIL'
        output = self._query(COMMAND)
        return output

    def get_sensor_information(self):
        """
        Return information about the type of sensor connected to
        the temperature controller, the type of temperature controller
        and the set temperature upper limit

        "T" type is for thermocouple

        Returns
        -------
        dry_bulb_sensor_type : str
        wet_bulb_sensor_type : str
        temperature_controller_type : str
        set_temperature_upper_limit : float
        """
        output = self._query('TYPE?')
        values = output.strip().split(',')
        return (*values[0:3], float(values[3]))

    def get_alarms(self):
        """
        Returns a list of alarm numbers, empty if there are no alarms

        A maximum of 16 alarms can be returned

        Returns
        -------
        alarms : list
        """
        output = self._query('ALARM?')
        alarms = [int(x) for x in output.strip().split(',')[1:]]
        return alarms

    def get_refrigerator_setpoint(self):
        """
        Return the refrigerator set point of the chamber

        0-8 : Manual mode
        9   : Auto mode

        Returns
        -------
        setpoint : int
        """
        output = self._query('SET?')
        # Parse response : 'REFx'
        print(output)
        return int(output[3:])
    
    def start_program(self, program):
        """
        Starts the specified program

        Parameters
        ----------
        program : int
        """
        assert_number(program)
        self._query(f'PRGM,RUN,RAM:{program:d},STEP1')
    
    def skip_one_step(self):
        """
        Skip the current step in the running program
        """
        output = self._query('PRGM,ADVANCE')

    def stop_program(self, end='STANDBY'):
        """
        Stop current program execution and apply specified end conditions

            HOLD : hold the current setpoints
            OFF : Turn off the unit
            STANDBY : Put the unit in standby mode (no regulation)
            CONST : Put the unit in constant mode
        """
        assert end in ['STANDBY', 'HOLD', 'OFF', 'CONST']
        output = self._query(f'PRGM,END,{end}')


    def pause_program(self):
        """
        Pauses program execution
        """
        output = self._query('PRGM,PAUSE')

    def continue_program(self):
        """
        Resume program execution
        """
        output = self._query('PRGM,CONTINUE')

    def set_panel_state(self, state : bool):
        """
        Turn on/off panel power

        Parameters
        ----------
        state : bool
        """
        output = self._query('POWER,' + ('ON' if state else 'OFF'))

    def set_temperature(self, temperature : float):
        """
        Configure the current temperature setpoint

        If 'OFF', temperature control is turned off

        Parameters
        ----------
        temperature : float or str
        """
        if isinstance(temperature, str):
            if temperature.upper() == OFF_KEYWORD.upper():
                self._prot.query(f'TEMP, SOFF')
        elif is_number(temperature):
            self._prot.query(f'TEMP, S{temperature}')
        else:
            raise ValueError(f"Invalid temperature type : {type(temperature)}")


    def set_humidity(self, humidity):
        """
        Configure the current humidity setpoint

        If 'OFF', humidity control is turned off

        Parameters
        ----------
        humidity : int or str
        """
        if isinstance(humidity, str):
            if humidity.upper() == OFF_KEYWORD.upper():
                self._prot.query(f'HUMI, SOFF')
        elif is_number(humidity):
            self._prot.query(f'HUMI, S{humidity}')
        else:
            raise ValueError(f"Invalid humidity type : {type(humidity)}")

    def set_refrigerator_state(self, state : bool):
        """
        Enables or disables the refigerator

        Parameters
        ----------
        state : bool
        """
        self._prot.query(f'SET, REF{2 if state else 0}')

    def test(self):
        """
        Test presence of the device
        """
        output = self._query('ROM?')
        # Easiest way to test for presence
        return 9 <= len(output) <= 20
