# Syndesi drivers Python package

This package contains all the official Syndesi Drivers

## Driver structure

```python
class DeviceName(Interfaces):
    def __init__(self, adapter : IAdapter) -> None:
        """
        Device description
        """
        super().__init__()

        # Check the adapter type here
        assert isinstance(adapter, ...), "Invalid adapter"

        # Use a protocol
        self._prot = SCPI(adapter)
        #self._prot = Raw(adapter)

    # Declare a method
    def my_method(self) -> int:
        """
        Method description
        """
        self._prot.write('...')
        data = self._prot.read('...')
        return int(data)
```