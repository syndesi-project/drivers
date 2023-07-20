# Siglent SDS1102CML oscilloscope driver
# Sébastien Deriaz
# 30.05.2023

from .. import IOscilloscope
from syndesi.adapters import IAdapter, Serial, VISA
from syndesi.protocols import SCPI
from enum import Enum
import re


# ACQW : Specifi

class SDS1102CML(IOscilloscope):
    def __init__(self, adapter : IAdapter) -> None:
        super().__init__()


        assert isinstance(adapter, Serial) or isinstance(adapter, VISA), "Invalid adapter"
        self._prot = SCPI(adapter)

    def set_time_scale(self, seconds_per_div : float):
        pass

    def set_voltage_scale(self, channel : int, volts_per_div : float):
        pass

    def set_coupling(self, channel : int, coupling : IOscilloscope.Coupling):
        coupling_match = {
            IOscilloscope.Coupling.AC : 'A1M',
            IOscilloscope.Coupling.DC : 'D1M',
            IOscilloscope.Coupling.GND : 'GND',

        }
        self._prot.write(f'C{channel}:CPL {coupling_match[coupling]}')

    def run_self_cal(self):
        out = self._prot.query('*CAL?')
        if out != '*CAL 0':
            raise RuntimeError('Self-calibration sequence failed, response : \'{out}\'')

    def clear_status_register(self):
        self._prot.write('*CLS')

    def read_error_register(self):
        """
        reads and clears the contents of
        the Command error Register (CMR)

        Returns
        -------
        code : int
        description : str
        """

        errorStatusRegisterStructure = {
            0 : 'No error',
            1 : 'Unrecognized command/query header',
            2 : 'Invalid character',
            3 : 'Invalid separator',
            4 : 'Missing parameter',
            5 : 'Unrecognized keyword',
            6 : 'String error',
            7 : 'Parameter cannot allowed',
            8 : 'Command String Too Long',
            9 : 'Query cannot allowed',
            10 : 'Missing Query mask',
            11 : 'Invalid parameter',
            12 : 'Parameter syntax error',
            13 : 'Filename too long'
        }
        out = self._prot.query('CMR?')
        # output is 'CMR x' with
        pattern = r'CMR [0-9]{1,2}'
        match = re.match(pattern, out)
        code = int(match.group(1))
        if code not in errorStatusRegisterStructure:
            raise ValueError('Invalid error code in response \'{out}\'')
        else:
            return code, errorStatusRegisterStructure[code]


    def save_csv(self):
        """
        TODO
        """
        pass

    def get_cymometer_value(self):
        """
        Queries the value of the cymometer
        When the signal frequency is less
        than 10Hz, it returns 10Hz.
        """
        out = self._prot.query('CYMOMETER?')
        # TODO : Convert 10Hz, 10kHz, 10Mhz, etc... to Hertz

    def force_trigger(self):
        """
        Causes the instrument to make one acquisition
        """
        self._prot.write('FORCE_TRIGGER')

    def set_filter_state(self, channel : int, state : bool):
        """
        Sets the filter state for the specified channel

        Parameters
        ----------
        channel : int
        state : bool
        """
        self._prot.write(f'C{channel}:FILT {"ON" if state else "OFF"}')
        

