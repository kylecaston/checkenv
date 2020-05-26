import pytest
import os
from jsonschema.exceptions import ValidationError
from checkenv import CheckEnv, EnvCheckResults, EnvCheckResultRow

dir_path = os.path.dirname(os.path.realpath(__file__))

def test_no_config_file():
    with pytest.raises(IOError):
        instance = CheckEnv()
        instance.load_spec_file()

def test_invalid_config():
    with pytest.raises(ValidationError):
        instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/invalid.json'))
        instance.load_spec_file()

def test_valid_config_loads():
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid1.json'))
    instance.load_spec_file()

def test_all_env_names_set_valid1(monkeypatch):
    monkeypatch.setenv("VALUE1", "value1")
    monkeypatch.setenv("VALUE2", "value2")
    monkeypatch.setenv("VALUE3", "value3")
    monkeypatch.setenv("VALUE4", "value4")
    monkeypatch.setenv("VALUE5", "value5")

    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid1.json'))
    instance.load_spec_file()
    instance.apply_spec()
    
    # nothing should be in mandatory or optional sets
    assert [] == instance.missing
    assert [] == instance.optional
    assert instance.check_failed == False

@pytest.fixture
def valid2_fresh_environment(monkeypatch):
    monkeypatch.delenv("VALUE1_NOT_SET", raising=False)
    monkeypatch.delenv("VALUE2_NOT_SET_WITH_DEFAULT", raising=False)
    monkeypatch.delenv("VALUE3_NOT_SET_NOT_REQUIRED", raising=False)

def test_mandatory_value_not_set_valid2(valid2_fresh_environment):
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
    instance.load_spec_file()
    instance.apply_spec()
    assert ['VALUE1_NOT_SET'] == instance.missing
    assert set(['VALUE3_NOT_SET_NOT_REQUIRED', 'VALUE2_NOT_SET_WITH_DEFAULT']) == set(instance.optional)

def test_default_mandatory_value_set(valid2_fresh_environment, monkeypatch):
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
    instance.load_spec_file()
    instance.apply_spec()
    assert os.getenv("VALUE2_NOT_SET_WITH_DEFAULT") == "3000"

def test_ensure_check_failed(valid2_fresh_environment):
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
    instance.load_spec_file()
    instance.apply_spec()
    assert instance.check_failed == True

# def test_print_results_color(valid2_fresh_environment, capsys):
#     instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
#     instance.load_spec_file()
#     instance.apply_spec()
#     instance.print_results(instance.missing, EnvCheckResults.MISSING)
#     stdout, err = capsys.readouterr()
#     with capsys.disabled():
#         print("stdout is: ", stdout)
    
#     assert err == ''

def test_plural_string_length_zero():
    default = EnvCheckResults(None, None, None)
    result = default._plural_string(0)
    assert result == "s are"

def test_plural_string_length_one():
    default = EnvCheckResults(None, None, None)
    result = default._plural_string(1)
    assert result == " is"

def test_plural_string_length_two():
    default = EnvCheckResults(None, None, None)
    result = default._plural_string(2)
    assert result == "s are"
