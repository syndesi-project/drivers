from syndesi.adapters import SerialPort, Adapter
from syndesi.protocols import Delimited
from syndesi.adapters import Timeout
from syndesi.adapters.timeout import TimeoutException 
from ..driver import Driver
from queue import Queue
import threading
# from syndesi.tools.types import assert_number
# from typing import Union, List
# from enum import Enum
import re
from time import sleep

# TODO : Implement single line commands

def _check_response(query, response):
    #assert response == query
    pass


class Actuator:
    def __init__(self, protocol : Delimited, updates : dict, messages_queue : Queue, letter : str, limits : tuple) -> None:
        self._letter = letter
        self._prot = protocol
        self._limits = limits
        self._updates = updates
        self._messages_queue = messages_queue

    def get_position(self):
        """
        Return current actuator position
        """
        raise NotImplementedError()

    def move_absolute(self, speed : int, position : float):
        """
        Move to an absolute position
        """
        pass

class LinearActuator(Actuator):
    def __init__(self, protocol : Delimited, updates : dict, messages_queue : Queue, letter : str, limits : tuple) -> None:
        super().__init__(protocol, updates, messages_queue, letter, limits)

    # Responses are not checked because the returned value will be received later

    def stop(self):
        """
        Stop the actuator
        """
        self._prot.write(f'${self._letter}0')

    def free_move_at_speed(self, speed : int):
        """
        Free move at constant speed. Movement can be stopped with stop()

        Parameters
        ----------
        speed : int
            Percentage (-100 to 100)
        """
        self._prot.write(f'$X1,{speed:.0f}')

    def move_relative(self, speed : int, distance : float):
        """
        Move relative distance (mm)
        
        Parameters
        ----------
        speed : int
            Percentage (1-100)
        distance : float
            Distance in millimiters
        """
        self._prot.write(f'${self._letter}2,{speed:.0f},{distance:.3f}')

    def move_absolute(self, speed : int, position : float):
        """
        Move to an absolute position (mm)

        Parameters
        ----------
        speed : int
            Percentage (1-100)
        position : float
        """
        self._prot.write(f'${self._letter}3,{speed:.0f},{position:.3f}')

    def move_relative_steps(self, speed : int, steps : int):
        """
        For debugging, move a relative number of steps

        Parameters
        ----------
        speed : int
            Percentage (1-100)
        steps : int
        """
        self._prot.write(f'${self._letter}4,{speed:.0f},{steps:d}')

    def auto_home(self):
        """
        Auto-home actuator
        """
        query = f'${self._letter}5'
        self._prot.write(query)

    def status(self):
        """
        Return actuator status

        Returns
        -------
        position : float
            Position in millimiters
        steps : int
            Step number
        homed : bool
        """
        query = f'${self._letter}6'
        self._prot.write(query)
        
        _check_response(query, response)
        # Read the data
        pattern = f'{self._letter}:(\w+),([0-9.]+),([0-9]+),([01])'
        match = re.match(pattern, data)
        return (
            float(match.group(2)),
            int(match.group(3)),
            bool(int(match.group(4)))
        )

    def get_position(self):
        """
        Get current position
        """
        return self.status()[0]

class RotaryActuator(Actuator):
    def __init__(self, protocol : Delimited, updates : dict, messages_queue : Queue, letter : str, limits : tuple) -> None:
        super().__init__(protocol, updates, messages_queue, letter, limits)

    # Responses are not checked because the returned value will be received later

    def stop(self):
        """
        Stop the actuator
        """
        self._prot.write(f'${self._letter}0')

    def free_move_at_speed(self, speed : int):
        """
        Free move at constant speed. Movement can be stopped with stop()

        Parameters
        ----------
        speed : int
            Percentage (-100 to 100)
        """
        self._prot.write(f'$X1,{speed:.0f}')

    def move_relative(self, speed : int, angle : float):
        """
        Move relative angle (degrees)
        
        Parameters
        ----------
        speed : int
            Percentage (1-100)
        angle : float
            Angle in degrees
        """
        self._prot.write(f'${self._letter}2,{speed:.0f},{angle:.3f}')

    def move_absolute(self, speed : int, angle : float):
        """
        Move to an absolute angle (degrees)

        Parameters
        ----------
        speed : int
            Percentage (1-100)
        angle : float
        """
        self._prot.write(f'${self._letter}3,{speed:.0f},{angle:.3f}')

    def move_relative_steps(self, speed : int, steps : int):
        """
        For debugging, move a relative number of steps

        Parameters
        ----------
        speed : int
            Percentage (1-100)
        steps : int
        """
        self._prot.write(f'${self._letter}4,{speed:.0f},{steps:d}')

    def auto_home(self):
        """
        Auto-home actuator
        """
        query = f'${self._letter}5'
        self._prot.write(query)
        
        _check_response(query, response)

    def status(self):
        """
        Return actuator status

        Returns
        -------
        angle : float
            Angle in degrees
        """
        query = f'${self._letter}6'
        with self._messages_queue.mutex:
            self._messages_queue.queue.clear()
        self._prot.write(query)
        # Get the message from the queue
        response = self._messages_queue.get()
        print(f'response : {response}')
        _check_response(query, response)
        # Read the data
        print('Waiting for data...')
        data = self._messages_queue.get()
        print(f'data : {data}')
        pattern = f'{self._letter}:(\w+),([0-9.]+)'
        match = re.match(pattern, data)
        if match is None:
            raise ValueError(f'Failed to parse : {data}')
        return float(match.group(2))

    def get_position(self):
        """
        Get current position
        """
        return self.status()

class RingIllumination:
    def __init__(self, protocol : Delimited) -> None:
        self._prot = protocol

    def _disable_all_colors(self):
        """
        Disable all colors, use set_colors instead
        """
        query = '$c7'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def _enable_all_colors(self):
        """
        Enable all colors, use set_colors instead
        """
        query = '$c8'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def set_colors(self, red : bool, green : bool, blue : bool, white : bool):
        """
        Set individual color LEDs on/off

        Parameters
        ----------
        red : bool
        green : bool
        blue : bool
        white : bool
        """
        colors_and_letters = {
            'R' : red,
            'G' : green,
            'B' : blue,
            'W' : white
        }
        for letter, color in colors_and_letters.items():
            query = f'$c{1 if color else 0},{letter}'
            response = self._prot.query(query)
            
            _check_response(query, response)

    def on(self):
        """
        Turn on ring illumination
        """
        query = '$c1'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def off(self):
        """
        TUrn off ring illumination
        """
        query = '$c0'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def adjust_intensity(self, percentage):
        """
        Ajust the intensity of all leds

        Parameters
        ----------
        percentage : int
        """
        query = f'$c2,{percentage:d}'
        response = self._prot.query(query)
        
        _check_response(query, response)
    
    def set_individual_leds(self, leds, status : bool):
        """
        Set the status of one or multiple LEDs

        Parameters
        ----------
        leds : int or list
        status : bool
        """
        if isinstance(leds, int):
            leds = [leds]
        
        for l in leds:
            assert 1 <= l <= 8
            query = f'$c3,{l},{1 if status else 0}'
        response = self._prot.query(query)

        _check_response(query, response)
        

    def enable_all_leds(self):
        """
        Enable all leds
        """
        query = '$c4'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def disable_all_leds(self):
        """
        Disable all leds (the device is still ON, but all LEDs are disabled)
        """
        query = '$c5'
        response = self._prot.query(query)
        
        _check_response(query, response)
    
    def status(self):
        """
        Return on/off state, intensity, active leds and color

        Returns
        -------
        on_off : bool
        intensity : int
        active_leds : leds
        color : dict
            red
            blue
            green
            white
        """
        query = '$c6'
        response = self._prot.query(query)
        
        _check_response(query, response)
        # Read the status data
        pattern = 'c:(\w+),([01]),([0-9]+),([0-9]+),([0-9]+)'
        match = re.match(pattern, data)
        
        # First element (I8 in my case) is unknown, ID ?
        color_integer = int(match.group(5))
        return (
            bool(int(match.group(2))),
            int(match.group(3)),
            [x+1 for x in range(8) if (int(match.group(4)) >>x) & 1], # Convert 8 bits to list of integers
            {
                'red' : bool(color_integer & 0b0001),
                'green' : bool(color_integer & 0b0010),
                'blue' : bool(color_integer & 0b0100),
                'white' : bool(color_integer & 0b1000)
            }
        )

class MatrixIllumination:
    def __init__(self, protocol : Delimited) -> None:
        self._prot = protocol

    def on(self):
        """
        Turn on matrix illumination
        """
        query = '$a1'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def off(self):
        """
        TUrn off ring illumination
        """
        query = '$a0'
        response = self._prot.query(query)
        
        _check_response(query, response)

    def adjust_intensity(self, percentage):
        """
        Ajust the intensity of all leds

        Parameters
        ----------
        percentage : int
        """
        query = f'$a2,{percentage:d}'
        response = self._prot.write(query)
        
        _check_response(query, response)
    
    def set_individual_columns(self, columns, status : bool):
        """
        Set the status of one or multiple columns

        Parameters
        ----------
        columns : int or list
        status : bool
        """
        if isinstance(columns, int):
            columns = [columns]
        
        for l in columns:
            assert 1 <= l <= 10
            query = f'$a3,{l},{1 if status else 0}'
            response = self._prot.write(query)
            
            _check_response(query, response)

    def enable_all_columns(self):
        """
        Enable all columns
        """
        query = '$a4'
        response = self._prot.write(query)
        
        _check_response(query, response)

    def disable_all_columns(self):
        """
        Disable all columns (the device is still ON, but all LEDs are disabled)
        """
        query = '$a5'
        response = self._prot.write(query)
        
        _check_response(query, response)
    
    def status(self):
        """
        Return on/off state, intensity and active columns

        Returns
        -------
        on_off : bool
        intensity : int
        active_columns : leds
        """

        # TODO : Fix this function, the returned data doesn't seem correct

        raise NotImplementedError()
        query = '$a6'
        self._prot.write(query)
        
        _check_response(query, response)
        # Read the status data
        pattern = 'c:(\w+),([01]),([0-9]+),([0-9]+),([0-9]+)'
        match = re.match(pattern, data)
        
        # First element (I8 in my case) is unknown, ID ?
        return (
            bool(int(match.group(2))),
            int(match.group(3)),
            [x+1 for x in range(8) if (int(match.group(4)) >>x) & 1], # Convert 8 bits to list of integers
        )

class SpotIllumination:
    def __init__(self, protocol : Delimited) -> None:
        self._prot = protocol

    def on(self):
        """
        Turn on spot illumination
        """
        query = '$b1'
        self._prot.write(query)
        
        _check_response(query, response)

    def off(self):
        """
        TUrn off spot illumination
        """
        query = '$b0'
        self._prot.write(query)
        
        _check_response(query, response)

    def adjust_intensity(self, percentage):
        """
        Ajust the intensity

        Parameters
        ----------
        percentage : int
        """
        query = f'$b2,{percentage:d}'
        self._prot.write(query)
        
        _check_response(query, response)
   
    def status(self):
        """
        Return on/off state and intensity

        Returns
        -------
        on_off : bool
        intensity : int
        """
        query = '$b6'
        self._prot.write(query)
        
        _check_response(query, response)
        # Read the status data
        pattern = 'b:(\w+),([01]),([0-9]+)'
        match = re.match(pattern, data)
        
        # First element (I1 in my case) is unknown, ID ?
        return (
            bool(int(match.group(2))),
            int(match.group(3))
        )




class MicroqubicMrcl700(Driver):
    # unit/s at 100% speed
    MAX_SPEEDS = {
        'A' : 180 / 37,
        'B' : 180 / 35.5,
        'C' : 120 / 7.5,
        'R' : 180 / 1,
        'X' : 70 / 4.5,
        'Y' : 70 / 4.5,
        'Z' : 120 / 7.5
    }
    ACTUATORS = {
        'A' : 'Camera tilt, primary axis',
        'B' : 'Camera tilt, secondary axis',
        'C' : 'Focus',
        'R' : 'Sample rotation',
        'X' : 'X axis',
        'Y' : 'Y axis',
        'Z' : 'Zoom'
    }

    def __init__(self, adapter : Adapter) -> None:
        """
        Microqubic MRCL700 3D microscope
        
        """
        super().__init__()

        assert isinstance(adapter, SerialPort), "Invalid adapter"
        self._prot = Delimited(adapter, termination='\r\n')
        self._positions = {}
        self._speeds = {k : 0 for k in self.ACTUATORS}

        # This dictionnary stores update flags for each actuatuor (position and speed)
        # A function can wait on one of these events to see if data was returned sucessfuly
        self._updates = {
            'positions' : {k : threading.Event() for k in self.ACTUATORS},
            'speeds' : {k : threading.Event() for k in self.ACTUATORS},
        }
        # This queue stores anything that couldn't be parsed by the thread
        self._messages_queue = Queue()

        # Since the microscope could send data whenever, a reading thread is here to
        # catch everything
        self._stop = [False]
        self._read_thread = threading.Thread(target=self.read_thread, args=(self._positions, self._speeds, self._prot, self._updates, self._messages_queue, self._stop))
        self._read_thread.start()

        # Accessories
        self.ring_illumination = RingIllumination(self._prot)
        self.matrix_illumination = MatrixIllumination(self._prot)
        self.spot_illumination = SpotIllumination(self._prot)
        self.A = RotaryActuator(self._prot, self._updates, self._messages_queue, 'A', (-90, 90))
        self.B = RotaryActuator(self._prot, self._updates, self._messages_queue, 'B', (-90, 90))
        self.C = LinearActuator(self._prot, self._updates, self._messages_queue, 'C', (0, 120))
        self.R = RotaryActuator(self._prot, self._updates, self._messages_queue, 'R', (-90, 90))
        self.X = LinearActuator(self._prot, self._updates, self._messages_queue, 'X', (0, 70))
        self.Y = LinearActuator(self._prot, self._updates, self._messages_queue, 'Y', (0, 70))
        self.Z = LinearActuator(self._prot, self._updates, self._messages_queue, 'Z', (0, 120))

        #self._positions = {getattr(self, k).get_position() for k in self.ACTUATORS}
        # for k in self.ACTUATORS:
        #     try:
        #         self._positions[k] = getattr(self, k).get_position()
        #     except Exception:
        #         pass
            #sleep(1)
        

    def stop_thread(self):
        if self._read_thread.is_alive():
            self._stop[0] = True
            self._read_thread.join()

    def __del__(self):
        print(f'__del__')
        self.stop_thread()
        self._prot._adapter.close()

    def read_thread(self, positions : dict, speeds : dict, prot : Delimited, updates : dict, messages_queue : Queue, stop : list):
        SPEED_PATTERN = '$(\w)1,([0-9.]+)'
        #STATUS_PATTERN = '(\w+):([0-9A-Za-z]+),([0-9\-.]+)(?:,([0-9\-]+),([01]))?'
        STATUS_PATTERN = '(\w+):([0-9A-Za-z]+),([0-9\-.]+),([0-9\-]+),([01])'

        def parse_and_set(positions : dict, speeds : dict, data):
            """
            Parse the command and return its letter and True if it is a status update,
            False if it is a speed update

            If the command cannot be parsed, ('',None) is returned
            Returns
            """
            # Check status first
            match = re.match(STATUS_PATTERN, data)
            if match is not None:
                letter = match.group(1)
                id = match.group(2)
                position = float(match.group(3))
                if match.group(4) is not None:
                    step_number = int(match.group(4))
                if match.group(5) is not None:
                    homed = bool(int(match.group(5)))

                positions[letter] = position
                print(f'->Status {position}')
                return letter, True

            match = re.match(SPEED_PATTERN, data)
            if match is not None:
                letter = match.group(1)
                speed = float(match.group(2))
                speeds[letter] = speed
                print(f'->Speed {speed}')
                return letter, False
            return '', None

        while not stop[0]:
            try:
                data = prot.read(timeout=Timeout(response=1, on_response='error'))
            except TimeoutException:
                pass
            else:
                print(f'Parsing "{data}" ...', end='')
                letter, is_status = parse_and_set(positions, speeds, data)
                if letter:
                    print(f'Success : {letter}')
                    # Parsing was a success, set the update flag
                    updates['positions' if is_status else 'speeds'][letter].set()
                else:
                    print('Fail, put in the queue')
                    # Parsing failed, put the data in the queue
                    messages_queue.put(data)


    def test(self):
        """
        Test if device is present

        This command uses the status led intensity command (without changing its value)
        """
        query = '$*8'
        self._prot.write(query)
        
        return response == query


    def auto_home(self):
        """
        Perform automatic homing
        """
        query = '$*5'
        self._prot.write(query)
        
        #_check_response(query, response)

    def emergency_stop(self):
        """
        Performs an emergency stop
        """
        query = '$*0'
        self._prot.write(query)
        
        #_check_response(query, response)

    def set_status_led_intensity(self, percentage):
        """
        returns the led stats
        """
        query = f'$*8,{percentage:d}'
        self._prot.write(query)
        
        #_check_response(query, response)

    def move_absolute(self, positions : dict, sync : bool = False):
        """
        Set the position of multiple actuators at a time.

        Movements can me synchronized by setting sync=True

        Available actuators are : A,B,C,R,X,Y,Z

        Parameters are passed as a dict in the form :
        {
            'A' : (position, speed)
            'R' : (position, speed)
            ...
        }

        Parameters
        ----------
        positions : dict
        sync : bool
            Synchronize movements, each speed will represent a multiplication factor of the new calculated speed.
        """
        times = {}
        positions = positions.copy()
        # Find the longest time. This is used for syncing the actuators (if used)
        print('Getting positions...')
        times = {k : (p - getattr(self, k).get_position()) / self.MAX_SPEEDS[k] for k, (p, _) in positions.items()}
        print(f'Times : {times}')
        longest_time = max(times.values())
        for k, (p, s) in positions.items():
            # Check if everything is doable
            actuator : Actuator
            actuator = getattr(self, k)
            if not (actuator._limits[0] <= p <= actuator._limits[1]):
                raise ValueError(f'Position {p} is out of limits {actuator._limits} for actuator {k}')
            if sync:
                # Scale each speed as a factor 
                actuator.move_absolute(s * times[k] / longest_time, p)
            else:
                actuator.move_absolute(s, p)