# Offline tests
from .siglent_sdm30x5 import SDM3055, SDM3045X, SDM3065X
from syndesi.adapters import IP

def test_instanciate():
    sdm3055 = SDM3055(IP('127.0.0.1'))
    sdm3045x = SDM3045X(IP('127.0.0.1'))
    sdm3065x = SDM3065X(IP('127.0.0.1'))

mm : SDM3055
mm = None

def test_initialize(adapter_ip_address):
    global mm
    if adapter_ip_address is None:
        raise ValueError("Please specify adapter_ip_address")
    mm = SDM3055(IP(address=adapter_ip_address))

def test_identification():
    global mm
    # Open an adapter and run the tests
    identification = mm.get_identification()
    assert 'SDM3055' in identification, "Invalid identification"
    assert mm.test()

def test_voltage():
    global mm
    # Run a voltage measurement and see if the value is valid
    voltage = mm.measure_dc_voltage()

def test_ip(adapter_ip_address):
    global mm
    # Check if the current IP is the same as the one used to connect to the device
    assert mm.get_current_ip_address() == adapter_ip_address, "IP Address does not match instanciation"


def test_no_errors():
    global mm
    error = mm.get_system_error()
    print(f"Error : {error}")