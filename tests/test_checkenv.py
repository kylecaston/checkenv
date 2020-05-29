import os
import pytest
from jsonschema.exceptions import ValidationError
from checkenv import check, CheckEnv, EnvCheckResults, EnvCheckResultRow
from checkenv.exceptions import CheckEnvException

dir_path = os.path.dirname(os.path.realpath(__file__))

@pytest.fixture
def init_env(monkeypatch):
    # list any environment variables that are set in any test
    monkeypatch.delenv("OPTIONAL_1", raising=False)
    monkeypatch.delenv("OPTIONAL_2", raising=False)
    monkeypatch.delenv("VALUE1_NOT_SET", raising=False)
    monkeypatch.delenv("VALUE2_NOT_SET_WITH_DEFAULT", raising=False)
    monkeypatch.delenv("VALUE3_NOT_SET_NOT_REQUIRED", raising=False)
    monkeypatch.delenv("VALUE_1", raising=False)
    monkeypatch.delenv("VALUE_2", raising=False)
    monkeypatch.delenv("VALUE_3", raising=False)
    monkeypatch.delenv("VALUE_4", raising=False)
    monkeypatch.delenv("VALUE_5", raising=False)

def test_main_import_different_filename_doesnt_exist_sys_exit(init_env):
    with pytest.raises(SystemExit) as exc:
        check()
    assert exc.type == SystemExit

def test_main_import_invalid_json_sys_exit(init_env):
    with pytest.raises(SystemExit) as exc:
        check(filename=os.path.join(dir_path, 'fixtures/invalid.json'))
    assert exc.type == SystemExit

def test_main_import_valid_json_checkenv_succeeds_and_continues(init_env, monkeypatch):
    check(filename=os.path.join(dir_path, 'fixtures/valid_no_mandatory.json'))

def test_main_import_valid_json_checkenv_fails_and_exits(init_env):
    with pytest.raises(SystemExit) as exc:
        check(filename=os.path.join(dir_path, 'fixtures/valid1.json'))
    assert exc.type == SystemExit

def test_main_import_raise_exception_on_error(init_env):
    with pytest.raises(CheckEnvException) as exc:
        check(filename=os.path.join(dir_path, 'fixtures/valid2.json'), raise_exception=True)
    assert exc.type == CheckEnvException

def test_main_import_raise_exception_on_error_details(init_env):
    try:
        check(filename=os.path.join(dir_path, 'fixtures/valid2.json'), raise_exception=True)
    except CheckEnvException as cee:
        assert cee.missing == ['VALUE1_NOT_SET']
        assert set(cee.optional) == set(['VALUE3_NOT_SET_NOT_REQUIRED', 'VALUE2_NOT_SET_WITH_DEFAULT'])

def test_no_config_file(init_env):
    with pytest.raises(IOError):
        instance = CheckEnv()
        instance.load_spec_file()

def test_invalid_config(init_env):
    with pytest.raises(ValidationError):
        instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/invalid.json'))
        instance.load_spec_file()

def test_valid_config_loads():
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid1.json'))
    instance.load_spec_file()

def test_all_env_names_set_valid1(init_env, monkeypatch):
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

def test_mandatory_value_not_set_valid2(init_env, monkeypatch):
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
    instance.load_spec_file()
    instance.apply_spec()
    assert ['VALUE1_NOT_SET'] == instance.missing
    assert set(['VALUE3_NOT_SET_NOT_REQUIRED', 'VALUE2_NOT_SET_WITH_DEFAULT']) == set(instance.optional)

def test_default_mandatory_value_set(init_env):
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
    instance.load_spec_file()
    instance.apply_spec()
    assert os.getenv("VALUE2_NOT_SET_WITH_DEFAULT") == "3000"

def test_ensure_check_failed(init_env):
    instance = CheckEnv(env_filename=os.path.join(dir_path, 'fixtures/valid2.json'))
    instance.load_spec_file()
    instance.apply_spec()
    assert instance.check_failed == True

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

def test_envcheckresultrow_constructor():
    env_name = 'FIELD_1'
    default = 'DEFAULT_1'
    description = 'DESCRIPTION_1'
    instance = EnvCheckResultRow(env_name, default=default, description=description)
    assert instance.name == env_name
    assert instance.default == default
    assert instance.description == description

def test_envcheckresultrow_repr_no_default_no_desc():
    env_name = 'FIELD_1'
    instance = EnvCheckResultRow(env_name)
    assert str(instance) == env_name

def test_envcheckresultrow_repr_default_no_desc():
    env_name = 'FIELD_1'
    default = 'DEFAULT_1'
    instance = EnvCheckResultRow(env_name, default=default)
    assert str(instance) == 'FIELD_1 (default=DEFAULT_1)'

def test_envcheckresultrow_repr_no_default_desc():
    env_name = 'FIELD_1'
    description = 'DESCRIPTION_1'
    instance = EnvCheckResultRow(env_name, description=description)
    assert str(instance) == 'FIELD_1 DESCRIPTION_1'

def test_envcheckresultrow_repr_default_desc():
    env_name = 'FIELD_1'
    default = 'DEFAULT_1'
    description = 'DESCRIPTION_1'
    instance = EnvCheckResultRow(env_name, default=default, description=description)
    assert str(instance) == 'FIELD_1 (default=DEFAULT_1) DESCRIPTION_1'
