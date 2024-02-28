"""Exception class for reporting back missing and optional values"""
from future import standard_library
standard_library.install_aliases()

class CheckEnvException(Exception):
    """my class here"""
    _missing = []
    _optional = []

    def __init__(self, missing, optional):
        self._missing = missing
        self._optional = optional

    @property
    def missing(self):
        """Pretty obvious, it's the missing values"""
        return self._missing

    @property
    def optional(self):
        return self._optional
