from future import standard_library
standard_library.install_aliases()

class CheckEnvException(Exception):
    _missing = []
    _optional = []

    def __init__(self, missing, optional):
        self._missing = missing
        self._optional = optional

    @property
    def missing(self):
        return self._missing

    @property
    def optional(self):
        return self._optional
