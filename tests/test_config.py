"""The TOML parameter file: types, ranges, and an error for every bad key or value."""

import math
import re
from pathlib import Path

import pytest

from bcsa_dcd.config import PARAMETERS, ConfigError, load
from helpers import write_config

REPO = Path(__file__).resolve().parent.parent
INTEGERS = {'nb_s', 'nb_cycles', 'limit_cycles', 'cycles_per_t'}


@pytest.fixture
def config(tmp_path):
    return lambda **overrides: write_config(tmp_path / 'config.toml', **overrides)


def test_shipped_config_is_valid():
    params = load(REPO / 'config.toml')
    assert list(params) == list(PARAMETERS)  # every key, in results-file order
    for key, value in params.items():
        assert type(value) is (int if key in INTEGERS else float), key


def test_integers_are_accepted_for_reals(config):
    params = load(config(T0=1000, sigma=0))
    assert params['T0'] == 1000.0 and type(params['T0']) is float
    assert params['sigma'] == 0.0 and type(params['sigma']) is float


@pytest.mark.parametrize('key, value', [
    ('nb_s', 1), ('nb_cycles', 1), ('limit_cycles', 0), ('cycles_per_t', 1),
    ('employed_bees_percentage', 1), ('employed_bees_percentage', 1e-9),
    ('T0', 1e-9), ('Tmin', 1e-9), ('alpha', 1e-9), ('alpha', 0.999),
    ('gamma', 0), ('gamma', 1), ('sigma', 0), ('sigma', 1), ('delta', 0), ('delta', 1),
])
def test_range_limits_are_accepted(key, value, config):
    assert load(config(**{key: value}))[key] == value


@pytest.mark.parametrize('key, value, message', [
    ('nb_s', 0, 'nb_s must be at least 1, got 0'),
    ('nb_cycles', 0, 'nb_cycles must be at least 1'),
    ('cycles_per_t', 0, 'cycles_per_t must be at least 1'),
    ('limit_cycles', -1, 'limit_cycles must be at least 0'),
    ('nb_s', 10.5, 'nb_s must be an integer'),
    ('nb_s', 10.0, 'nb_s must be an integer'),
    ('nb_s', '10', 'nb_s must be an integer'),
    ('nb_s', True, 'nb_s must be an integer'),
    ('employed_bees_percentage', 0, 'employed_bees_percentage must be in (0, 1]'),
    ('employed_bees_percentage', 1.5, 'employed_bees_percentage must be in (0, 1]'),
    ('T0', 0, 'T0 must be greater than 0'),
    ('Tmin', 0, 'Tmin must be greater than 0'),
    ('Tmin', -1.0, 'Tmin must be greater than 0'),
    ('alpha', 0, 'alpha must be in (0, 1)'),
    ('alpha', 1, 'alpha must be in (0, 1)'),  # never cools down: the run would not end
    ('gamma', 1.5, 'gamma must be in [0, 1]'),
    ('sigma', -0.1, 'sigma must be in [0, 1]'),
    ('delta', 1.1, 'delta must be in [0, 1]'),
    ('gamma', '0.8', 'gamma must be a finite number'),
    ('gamma', True, 'gamma must be a finite number'),
    ('T0', math.inf, 'T0 must be a finite number'),
    ('alpha', math.nan, 'alpha must be a finite number'),
])
def test_bad_values_are_rejected(key, value, message, config):
    with pytest.raises(ConfigError, match=re.escape(message)):
        load(config(**{key: value}))


def test_missing_keys_are_listed(config):
    with pytest.raises(ConfigError, match='missing alpha, gamma'):
        load(config(alpha=None, gamma=None))


def test_unknown_key(config):
    with pytest.raises(ConfigError, match='unknown key colour'):
        load(config(colour=1))


def test_nb_exec_points_to_runs(config):
    with pytest.raises(ConfigError, match='nb_exec is no longer a parameter.*--runs'):
        load(config(nb_exec=2))


def test_tables_are_unknown_keys(tmp_path, config):
    path = Path(config())
    path.write_text(path.read_text() + '[bees]\nscouts = 3\n')
    with pytest.raises(ConfigError, match='unknown key bees'):
        load(path)


def test_every_problem_is_reported_at_once(config):
    with pytest.raises(ConfigError) as error:
        load(config(nb_s=0, alpha=1, delta=None, colour=1))
    for part in ['unknown key colour', 'missing delta', 'nb_s must be', 'alpha must be']:
        assert part in str(error.value)


@pytest.mark.parametrize('content', [b'nb_s = = 1\n', b'nb_s = 1\nnb_s = 2\n', b'\xff\xfe\n'],
                         ids=['syntax', 'duplicate key', 'not UTF-8'])
def test_unreadable_toml(content, tmp_path):
    path = tmp_path / 'config.toml'
    path.write_bytes(content)
    with pytest.raises(ConfigError, match='not valid TOML'):
        load(path)
