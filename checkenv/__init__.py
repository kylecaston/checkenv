"""This module includes the logic for checkenv functionality."""

import json
import os
import sys
from typing import Any

from colorama import Back, Fore, Style, init
from jsonschema import validate
from jsonschema.exceptions import ValidationError

from checkenv.exceptions import CheckEnvException

init()


_DEFAULT_NOT_PROVIDED = object()
EnvDefault = str | int | float | bool


class EnvCheckResultRow:
    """Utilty class to keep track of environment variable specs.

    It was primarily written to make it easier to print color text to console."""

    def __init__(
        self,
        env_name: str,
        default: EnvDefault | None = None,
        description: str | None = None,
    ) -> None:
        self._env_name = env_name
        self._default = default
        self._description = description

    def __repr__(self) -> str:
        # {name} {(default=...)} {description}
        row_string = self._env_name
        if self._default is not None:
            row_string += f" (default={self._default})"
        if self._description:
            row_string += f" {self._description}"
        return row_string

    @property
    def name(self) -> str:
        """The environment variable name"""
        return self._env_name

    @property
    def default(self) -> EnvDefault | None:
        """The default value for the environment variable, if provided"""
        return self._default

    @property
    def description(self) -> str | None:
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

    def __init__(self, env_var_names: list[str], spec: dict[str, Any], section: str) -> None:
        self._env_var_names = env_var_names
        self._spec = spec
        self._section = section

    def __repr__(self) -> str:
        result = self.header
        for row in self.rows:
            result += "\n" + str(row)
        return result

    def _plural_string(self, length: int) -> str:
        """A cheap way to pluralize the header text"""
        return " is" if length == 1 else "s are"

    @property
    def header(self) -> str:
        """Returns a header string summarizing the environment variables for this section"""
        suffix = "required" if self._section == self.MISSING else "missing (but optional)"
        length = len(self._env_var_names)
        plural = self._plural_string(length)
        return f"The following {length} environment variable{plural} {suffix}"

    def _single_row(self, name: str) -> EnvCheckResultRow:
        """Encapsulates a single row as a EnvCheckResultRow object."""
        default = None
        desc = None
        if isinstance(self._spec[name], dict):
            default = self._spec[name].get("default", None)
            desc = self._spec[name].get("description", None)
        return EnvCheckResultRow(name, default, desc)

    @property
    def rows(self) -> list[EnvCheckResultRow]:
        """Returns a list of objects that represent individual rows.

        These are returned as objects so they can be used (logged, printed,
        to the console in color, etc. later)
        """
        return list(map(self._single_row, self._env_var_names))

    def print_console_color(self) -> None:
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
        print(self.header, end="")
        print(self._COLORS_RESET)
        for row in self.rows:
            print(self._COLORS_ENV_NAME_TEXT, end="")
            print(row.name, end="")
            print(self._COLORS_RESET, end="")
            if row.default is not None:
                print(self._COLORS_DEFAULT_TEXT, end="")
                print(f" (default={row.default})", end="")
                print(self._COLORS_RESET, end="")
            if row.description:
                print(f" {row.description}", end="")
            print(self._COLORS_RESET)


class CheckEnv:
    """Class to manage the steps to load and check an environment to ensure
    that environment variables are set appropriately.
    """

    # the acceptable schema for env_filename
    _schema = {
        "type": "object",
        "patternProperties": {
            "^[a-zA-Z_]+[a-zA-Z0-9_]*$": {
                "oneOf": [
                    {
                        "type": "object",
                        "properties": {
                            "required": {"type": "boolean"},
                            "description": {"type": "string"},
                            "default": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "number"},
                                    {"type": "boolean"},
                                ]
                            },
                        },
                        "additionalProperties": False,
                    },
                    {"type": "boolean"},
                ]
            },
        },
        "additionalProperties": False,
    }

    def __init__(self, env_filename: str = "env.json") -> None:
        self._env_filename = env_filename
        self._spec: dict[str, Any] | None = None
        self._missing: list[str] = []
        self._optional: list[str] = []

    def _reset(self) -> None:
        """Resets missing and optional lists"""
        self._missing = []
        self._optional = []

    def load_spec_file(self) -> None:
        """Loads the env var spec file, verifies it adheres to JSON schema

        Raises jsonschema.exceptions.ValidationError if input env.json file is malformed.
        Raises FileNotFoundError if the spec file cannot be found.
        """
        self._reset()
        with open(self._env_filename, encoding="utf-8") as jsonfile:
            jdata = json.load(jsonfile)
            validate(jdata, self._schema)
            self._spec = jdata

    def _check_and_set(
        self,
        name: str,
        required: bool,
        default: EnvDefault | object = _DEFAULT_NOT_PROVIDED,
    ) -> None:
        """Applies the spec against a single environment variable.

        If an environment variable is not set and a default value is provided,
        this method will apply the default value and mark the environment
        variable as optional.
        """
        # see if name is defined
        value = os.getenv(name, None)
        if value is None:
            if default is not _DEFAULT_NOT_PROVIDED:
                os.environ[name] = str(default)
                self._optional.append(name)
            else:  # see if this was mandatory or optional
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
        if self._spec is None:
            raise RuntimeError("Cannot apply checkenv spec before loading a spec file")

        for key, value in self._spec.items():
            if isinstance(value, bool):
                self._check_and_set(key, value)
            else:
                default = value.get("default", _DEFAULT_NOT_PROVIDED)
                self._check_and_set(key, value.get("required", True), default)

    @property
    def check_failed(self) -> bool:
        """Indicates whether or not the environment variable check has failed.

        :return: Returns True if any mandatory environment variables are not set; False otherwise
        :rtype: bool
        """
        return len(self._missing) > 0

    @property
    def missing(self) -> list[str]:
        """Returns a list of environment variables that are missing from the runtime environment"""
        return self._missing

    @property
    def optional(self) -> list[str]:
        """Returns a list of environment variables that were not defined in the runtime environment,
        but are optional.
        """
        return self._optional

    def print_results(self, env_var_names: list[str], section: str) -> None:
        """Consolidates the results of the checkenv process into a resulting object that can be
        output in a variety of different formats, such as colorized console output, or to something
        more structure, like a python logger.
        """
        if len(env_var_names) == 0:
            return
        results = EnvCheckResults(env_var_names, self._spec, section)
        results.print_console_color()


def _handle_exit(raise_exc: bool = False, exc: Exception | None = None) -> None:
    if not raise_exc:
        sys.exit(1)
    if exc is None:
        raise RuntimeError("checkenv exited without an exception")
    raise exc


def _handle_print(no_out: bool = False, msg: str = "") -> None:
    if not no_out:
        print(msg)


def check(
    filename: str = "env.json", raise_exception: bool = False, no_output: bool = False
) -> None:
    """Executes the end-to-end flow for checking environment variables against the spec.

    For most out-of-the-box applications, this is the only method you need to call.

    :param filename: The name of the environment configuration file (default, env.json)
    :type filename: str, optional
    :param raise_exception: If validation fails, raise an Exception instead of exiting
    :type raise_exception: bool, optional
    :param no_output: Do not write anything to stdout
    :type no_output: bool, optional
    """
    # handle two exception cases above
    try:
        env = CheckEnv(env_filename=filename)
        env.load_spec_file()
        env.apply_spec()
        if not no_output:
            env.print_results(env.missing, EnvCheckResults.MISSING)
            env.print_results(env.optional, EnvCheckResults.OPTIONAL)
        if env.check_failed:
            if raise_exception:
                raise CheckEnvException(env.missing, env.optional)
            _handle_exit(raise_exc=raise_exception)
    except ValidationError as validation_error:
        _handle_print(no_out=no_output, msg=validation_error.message)
        _handle_exit(raise_exc=raise_exception, exc=validation_error)
    except OSError as ioe:
        abs_filename = os.path.abspath(filename)
        _handle_print(
            no_out=no_output,
            msg=f'Unable to find checkenv configuration file "{abs_filename}" - exiting',
        )
        _handle_exit(raise_exc=raise_exception, exc=ioe)
