ARGUMENTS = {
    'adapter_ip_address' : str,
    'adapter_ip_port' : int,
    'debug_level' : None
}

# It is necessary to have defaults for each type, otherwise an error will be raised
# This default will be overwritten in pytest_generate_tests by a None if the default has been set
DEFAULTS = {
    str : 'default',
    int : float('nan')
}

def pytest_addoption(parser):
    for name, _type in ARGUMENTS.items():
        if _type is None:
            parser.addoption(f'--{name}', action='store_true')
        else:
            parser.addoption(f'--{name}', action='store', default=DEFAULTS[_type], type=_type)

def pytest_generate_tests(metafunc):
    # This is called for every test. Only get/set command line arguments
    # if the argument is specified in the list of test "fixturenames".
    for name, _type in ARGUMENTS.items():
        option_value = getattr(metafunc.config.option, name)
        if name in metafunc.fixturenames and option_value is not None:
            if option_value == DEFAULTS[_type]:
                option_value = None
            metafunc.parametrize(name, [option_value])