"""This module includes the logic for checkenv functionality."""
import os
import sys
import json
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from colorama import init, Fore, Back, Style
init()


class EnvCheckResultRow:
    """Utilty class to keep track of environment variable specs.

    It was primarily written to make it easier to print color text to console."""
    _env_name = None
    _default = None
    _description = None

    def __init__(self, env_name, default=None, description=None):
        self._env_name = env_name
        self._default = default
        self._description = description


    def __repr__(self):
        # {name} {(default=...)} {description}
        row_string = self._env_name
        if self._default:
            row_string += f' (default={self._default})'
        if self._description:
            row_string += f' {self._description}'
        return row_string

    @property
    def name(self):
        """The environment variable name"""
        return self._env_name

    @property
    def default(self):
        """The default value for the environment variable, if provided"""
        return self._default

    @property
    def description(self):
        """A description of the environment variable, if provided"""
        return self._description


class EnvCheckResults:
    """Utility class to encapsulate the objects and properties necessary for
    sharing and customizing the results of the checkenv process.
    """
    # constants for printing messages in color
    _COLORS_HEADER_MANDATORY = Back.RED + Fore.WHITE
    _COLORS_HEADER_OPTIONAL = Back.YELLOW + Fore.BLACK
    _COLORS_ENV_NAME_TEXT = Fore.BLUE
    _COLORS_DEFAULT_TEXT = Fore.YELLOW
    _COLORS_RESET = Style.RESET_ALL

    # pseudo-enums for class initialization
    MISSING = "missing"
    OPTIONAL = "optional"

    _env_var_names = []
    _spec = {}
    _section = None

    def __init__(self, env_var_names: list, spec: dict, section: str):
        self._env_var_names = env_var_names
        self._spec = spec
        self._section = section


    def __repr__(self):
        result = self.header
        for row in self.rows:
            result += '\n' + str(row)
        return result


    def _plural_string(self, length):
        """A cheap way to pluralize the header text"""
        return ' is' if length == 1 else 's are'


    @property
    def header(self) -> str:
        """Returns a header string summarizing the environment variables for this section"""
        suffix = 'required' if self._section == self.MISSING else 'missing (but optional)'
        length = len(self._env_var_names)
        plural = self._plural_string(length)
        return f'The following {length} environment variable{plural} {suffix}'


    def _single_row(self, name) -> str:
        """Encapsulates a single row as a EnvCheckResultRow object."""
        default = None
        desc = None
        if isinstance(self._spec[name], dict):
            default = self._spec[name].get('default', None)
            desc = self._spec[name].get('description', None)
        return EnvCheckResultRow(name, default, desc)


    @property
    def rows(self) -> list:
        """Returns a list of objects that represent individual rows.

        These are returned as objects so they can be used (logged, printed,
        to the console in color, etc. later)
        """
        return list(map(self._single_row, self._env_var_names))


    def print_console_color(self):
        """Prints the results of the checkenv process to the console using
        ANSI colors.

        This is the classic visual from the npm checkenv module.
        """
        header_color = None
        if self._section == self.MISSING:
            header_color = self._COLORS_HEADER_MANDATORY
        else:
            header_color = self._COLORS_HEADER_OPTIONAL
        
        print(header_color)
        print(self.header, end='')
        print(self._COLORS_RESET)
        for row in self.rows:
            print(self._COLORS_ENV_NAME_TEXT, end='')
            print(row.name, end='')
            print(self._COLORS_RESET, end='')
            if row.default:
                print(self._COLORS_DEFAULT_TEXT, end='')
                print(f' (default={row.default})', end='')
                print(self._COLORS_RESET, end='')
            if row.description:
                print(f' {row.description}', end='')
            print(self._COLORS_RESET)



class CheckEnv:
    """Class to manage the steps to load and check an environment to ensure
    that environment variables are set appropriately.
    """

    # filename for the JSON file that specified env vars
    _env_filename: str = None
    # the env variable spec to test against
    _spec: dict = None
    # list of env variable names that are missing and required
    _missing: list = []
    # list of env variable names that are missing but optional
    _optional: list = []
    # the acceptable schema for env_filename
    _schema: dict = {
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
                                    {"type": "string"},
                                    {"type": "number"},
                                    {"type": "boolean"}
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


    def __init__(self, env_filename='env.json'):
        self._env_filename = env_filename


    def load_spec_file(self) -> None:
        """Loads the env var spec file, verifies it adheres to JSON schema

        Raises os.ValidationError if the input env.json file is malformed.
        Raises IOError if the spec file cannot be found.
        """
        with open(self._env_filename) as jsonfile:
            jdata = json.load(jsonfile)
            validate(jdata, self._schema)
            self._spec = jdata


    def _check_and_set(self, name: str, required: bool, default=None) -> None:
        """Applies the spec against a single environment variable.

        If an environment variable is not set and a default value is provided,
        this method will apply the default value and mark the environment
        variable as optional.
        """
        # see if name is defined
        value = os.environ.get(name)
        if not value:
            if default: # if we have a default value, set as a str and continue
                os.environ[name] = str(default)
                self._optional.append(name)
            else:   # see if this was mandatory or optional
                if required:
                    self._missing.append(name)
                else:
                    self._optional.append(name)


    def apply_spec(self) -> None:
        """Iterate over the spec definitions and apply against the current environment.

        Determines the mandatory and optional environment variables.

        Applies any default values (if supplied, and if the the environment variable
        isn't already set.
        """
        # _self.spec is a dictionary with each key representing an env to check
        # 'key' is the environment variable name
        # 'value' is either a boolean to indicate required, or a dict with more params
        for key, value in self._spec.items():
            if isinstance(value, bool):
                self._check_and_set(key, value)
            else:
                self._check_and_set(key, value.get('required', True), value.get('default', None))


    @property
    def check_failed(self) -> bool:
        """Indicates whether or not the environment variable check has failed.

        :return: Returns True if any mandatory environment variables are not set; False otherwise
        :rtype: bool
        """
        if len(self._missing) > 0:
            return True
        return False


    @property
    def missing(self) -> list:
        """Returns a list of environment variables that are missing from the runtime environment"""
        return self._missing


    @property
    def optional(self) -> list:
        """Returns a list of environment variables that were not defined in the runtime environment,
        but are optional.
        """
        return self._optional


    def print_results(self, env_var_names: list, section: str) -> None:
        """ Consolidates the results of the checkenv process into a resulting object that can be
        output in a variety of different formats, such as colorized console output, or to something
        more structure, like a python logger.
        """
        if len(env_var_names) == 0:
            return
        results = EnvCheckResults(env_var_names, self._spec, section)
        results.print_console_color()


def check(filename: str = 'env.json'):
    """Executes the end-to-end flow for checking environment variables against the spec.

    For most out-of-the-box applications, this is the only method you need to call.
    """
    # handle two exception cases above
    try:
        env = CheckEnv(env_filename=filename)
        env.load_spec_file()
        env.apply_spec()
        env.print_results(env.missing, EnvCheckResults.MISSING)
        env.print_results(env.optional, EnvCheckResults.OPTIONAL)
        if env.check_failed:
            sys.exit()
    except ValidationError as validation_error:
        print(validation_error.message)
        sys.exit()
    except IOError:
        print(f'Unable to find checkenv configuration file "{filename}" - exiting')
        sys.exit()


# if __name__ == "__main__":
#     check()
#     print('asdfasdfa')
#     print('asdfdasdfasdfasdfasdf')
