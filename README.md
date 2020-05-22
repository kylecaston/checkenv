# checkenv

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

![Screenshot](https://github.com/kylecaston/checkenv/raw/master/docs/usage.png)

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
### 1.0.0
* Initial release
