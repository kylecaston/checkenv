import os
import sys
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from colorama import init, Fore, Back, Style
init()

COLORS_MANDATORY_HEADER = Back.RED + Fore.WHITE
COLORS_OPTIONAL_HEADER = Back.YELLOW + Fore.BLACK
COLORS_ENV_NAME_TEXT = Fore.BLUE
COLORS_DEFAULT_TEXT = Fore.YELLOW
COLORS_RESET = Style.RESET_ALL

_data = None
_missing = []   # list of env variable names that are missing and required
_optional = []  # list of env variable names that are missing but optional

_schema = {
    "type": "object",
    "patternProperties": {
        "^[a-zA-Z_]+[a-zA-Z0-9_]*$": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "required": {
                            "type": "boolean"
                        },
                        "description": {
                            "type": "string"
                        },
                        "default": {
                            "anyOf": [
                                { "type": "string" },
                                { "type": "number" },
                                { "type": "boolean" }
                            ]
                        }
                    }
                },
                {
                    "type": "boolean"
                }
            ]
        },
    },
    "additionalProperties": False
}

def _load_data(envfile):
    # search for env.json file - exist if not found
    try:
        with open('env.json') as envjson:
            jdata = json.load(envjson)
            
            # validate input JSON against supported schema for environment variables
            try:
                validate(jdata, _schema)
            except ValidationError as e:
                raise Exception(e.message)
            
            global _data
            _data = jdata
    except IOError:
        raise Exception(f'Unable to find checkenv configuration file "{envfile}" - exiting')

def _check_and_set(name, required, default=None):
    # see if name is defined
    value = os.environ.get(name)
    if not value:
        if default: # if we have a default value, set it and continue
            os.environ[name] = str(default)
            _optional.append(name)
        else:   # see if this was mandatory or optional
            if required:
                return _missing.append(name)
            else:
                return _optional.append(name)


def _check_env():
    # _data is a dictionary with each key representing an env to check
    # foreach key:
    #   1) if the value is a boolean (and true), then it's a simple value to check
    #   2) if the value is an object, check to see if `required` is true
    for key, value in _data.items():
        if type(value) == bool:
            _check_and_set(key, value)
        else:
            _check_and_set(key, value.get('required', True), value.get('default', None))


def _print_env_var(name):
    default = None
    desc = None
    if type(_data[name]) is dict:
        default = _data[name].get('default', None)
        desc = _data[name].get('description', None)

    # {name} {(default=...)} {description}
    print(COLORS_ENV_NAME_TEXT, end='')
    print(name, end='')
    print(COLORS_RESET, end='')
    if default:
        print(COLORS_DEFAULT_TEXT, end='')
        print(f' (default={default})', end='')
        print(COLORS_RESET, end='')
    if desc:
        print(f' {desc}', end='')
    print()


def _plural_string(length):
    return ' is' if length==1 else 's are'


def _print_optional(names):
    l = len(names)
    if l == 0:
        return

    print(COLORS_OPTIONAL_HEADER)
    print(f'The following {l} environment variable{_plural_string(l)} missing (but optional)', end='')
    print(COLORS_RESET)
    for n in names:
        _print_env_var(n)


def _print_mandatory(names):
    l = len(names)
    if l == 0:
        return

    print(COLORS_MANDATORY_HEADER)
    print(f'The following {l} environment variable{_plural_string(l)} required', end='')
    print(COLORS_RESET)
    for n in names:
        _print_env_var(n)


def check(envfile='env.json'):
    try:
        _load_data(envfile)
        _check_env()
        _print_mandatory(_missing)
        _print_optional(_optional)
        if len(_missing) > 0:
            sys.exit()
    except Exception as e:
        print(e)
        sys.exit()
