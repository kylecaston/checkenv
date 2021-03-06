# checkenv

[![PyPI](https://img.shields.io/pypi/v/checkenv?style=flat-square)](https://pypi.org/project/checkenv)
[![Python versions](https://img.shields.io/pypi/pyversions/checkenv)](https://img.shields.io/pypi/pyversions/checkenv)
[![CircleCI](https://circleci.com/gh/kylecaston/checkenv.svg?style=shield)](https://circleci.com/gh/kylecaston/checkenv)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/checkenv?style=flat-square)](https://pypistats.org/packages/checkenv)
[![PyPI - License](https://img.shields.io/pypi/l/checkenv?style=flat-square)](https://opensource.org/licenses/MIT)
[![Coverage Status](https://coveralls.io/repos/github/kylecaston/checkenv/badge.svg?branch=master)](https://coveralls.io/github/kylecaston/checkenv?branch=master)

A modern best-practice is to [store your application's configuration in environmental variables](http://12factor.net/config).  This allows you to keep all config data outside of your repository, and store it in a standard, system-agnostic location.  Modern build/deploy/development tools make it easier to manage these variables per-host, but they're still often undocumented, and can lead to bugs when missing.

This module lets you define all the environmental variables your application relies on in an `env.json` file.  It then provides a method to check for these variables at application launch, and print a help screen if any are missing.

Inspired from the popular npm package, [checkenv](https://www.npmjs.com/package/checkenv).

## Usage
First, define a JSON file called `env.json` in your project root (see below for the specific structure). Next, install the library using `pip` connected to the [PyPi](https://pypi.org/) index:
```bash
pip install checkenv
```

Then, add the following line to the top of your project's entry file:

```python
from checkenv import check
check()
```

By default, `checkenv` will print a pretty error message and call `sys.exit()` if any required variables are missing. It will also print an error message if optional variables are missing, but will not exit the process.

![Screenshot](https://raw.githubusercontent.com/kylecaston/checkenv/master/docs/usage.png)

You can specify a filename other than `env.json` by setting the optional parameter `filename`.  The library will attempt to load this file from the root path of your project.  You can also specify an absolute file path.

If you would like to handle errors yourself, `check` takes an optional `raise_exception` argument which causes it to raise exceptions instead of exiting the process.  

```python
from checkenv import check
try:
  check(raise_exception=True)
except Exception as e:
  # do something with the error 'e' because the process will not exit
```

An exception can be one of three classes of Exceptions:
* `checkenv.exceptions.CheckEnvException` - thrown if any mandatory environment variables are missing; contains `missing` and `optional` properties that contain a list of environment variable names
* `jsonschema.exceptions import ValidationError` - thrown if the input JSON files is invalid
* `IOError` - thrown if the input JSON file cannot be found

You can also silence any output to `stdout` by setting the optional parameter `no_output=True`.  It is recommended to use this in conjunction with `raise_exception=True` and handling the error yourself; otherwise, your application can fail silently because you do not realize that something is wrong with your environment variables.

## Configuration
Your JSON file should define the environmental variables as keys, and either a boolean (required) as the value, or a configuration object with any of the options below.

### JSON
```json
{
  "ENVIRONMENT": {
    "description": "This defines the current environment"
  },
  "PORT": {
    "description": "This is the port the API server will run on",
    "default": 3000
  },
  "PYTHON_PATH": true,
  "DEBUG": {
    "required": false,
    "description": "If set, enables additional debug messages"
  }
}
```

### Object Properties
* `required` - Defines whether or not this variable is required. By default, all variables are required, so you must explicitly set them to optional by setting this to `false`.
* `description` - Describes the variable and how it should be used. Useful for new developers setting up the project, and is printed in the error output if present.
* `default` - Defines the default value to use if variable is unset. Implicitly sets `required` to `false` regardless of any specified value.

## Change Log
### 1.2.0
* Added ability for `check()` to throw exceptions instead of killing the running process with `raise_exception=True`
* Added ability to silence all output to `stdout` with `no_output=True`
* Updated documentation with the `filename` parameter feature that allows you to specify an input JSON file with a different name than `env.json`
* Updated README.md with usage instructions for these new features
* Increased code coverage to 95%+

### 1.1.0
* Expanded supported Python interpreter versions - `checkenv` now supports Python versions 2.7, 3.5, 3.6, 3.7, and 3.8.
* Refactored the code with classes - although this does not add additional functionality, the code is cleaner, easier to understand, and better documented for future improvements
* Added tests with `pytest` and `tox`
* Every pushed branch undergoes automated testing with CircleCI 
* Started tracking code coverage percentage and currently hovering around ~50% (to be improved)

### 1.0.0
* Initial release
