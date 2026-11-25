"""Algorithm parameters: read from a TOML file and checked before any run."""

import math
import tomllib


class ConfigError(ValueError):
    """The parameters are unreadable, incomplete or out of range."""


def _integer(minimum):
    return int, lambda x: x >= minimum, f'at least {minimum}'


def _real(check, allowed):
    return float, check, allowed


# Every key, in results-file order: (type, range check, the range in words). The ranges
# exclude values that crash or never end (alpha >= 1 with T0 > Tmin cools forever).
PARAMETERS = {
    'nb_s': _integer(1),
    'nb_cycles': _integer(1),
    'limit_cycles': _integer(0),
    'employed_bees_percentage': _real(lambda x: 0 < x <= 1, 'in (0, 1]'),
    'T0': _real(lambda x: x > 0, 'greater than 0'),
    'Tmin': _real(lambda x: x > 0, 'greater than 0'),
    'alpha': _real(lambda x: 0 < x < 1, 'in (0, 1)'),
    'cycles_per_t': _integer(1),
    'gamma': _real(lambda x: 0 <= x <= 1, 'in [0, 1]'),
    'sigma': _real(lambda x: 0 <= x <= 1, 'in [0, 1]'),
    'delta': _real(lambda x: 0 <= x <= 1, 'in [0, 1]'),
}

# Keys that used to exist, and what replaced them.
REMOVED = {'nb_exec': 'the number of runs is the --runs option'}


def load(path):
    """Read and check the TOML file at path; return the parameters as a dict."""
    try:
        with open(path, 'rb') as file:
            raw = tomllib.load(file)
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f'not valid TOML: {error}') from None
    except UnicodeDecodeError:
        raise ConfigError('not valid TOML: the file is not UTF-8 text') from None
    return validate(raw)


def validate(raw):
    """Check every key of raw; return them typed (ints as int, reals as float)."""
    problems = []
    params = {}
    for key in raw:
        if key in REMOVED:
            problems.append(f'{key} is no longer a parameter: {REMOVED[key]}')
        elif key not in PARAMETERS:
            problems.append(f'unknown key {key}')
    missing = [key for key in PARAMETERS if key not in raw]
    if missing:
        problems.append('missing ' + ', '.join(missing))

    for key, (kind, in_range, allowed) in PARAMETERS.items():
        if key not in raw:
            continue
        value = raw[key]
        # bool is a subclass of int in Python, but true/false is never a number here.
        if kind is int and (isinstance(value, bool) or not isinstance(value, int)):
            problems.append(f'{key} must be an integer, got {value!r}')
        elif kind is float and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            problems.append(f'{key} must be a finite number, got {value!r}')
        elif not in_range(value):
            problems.append(f'{key} must be {allowed}, got {value!r}')
        else:
            params[key] = kind(value)

    if problems:
        raise ConfigError('; '.join(problems))
    return params
