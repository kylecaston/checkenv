import pytest
from checkenv import CheckEnv

def test_no_config_file():
    with pytest.raises(FileNotFoundError):
        instance = CheckEnv()
        instance.load_spec_file()

