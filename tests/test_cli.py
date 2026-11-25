"""The bcsa-dcd command line: options, input errors and entry points.

test_smoke.py checks the results file and the plots of a full run; these tests check what
each option changes, and that bad input stops with a usage error before any file is written.
"""

import logging
import subprocess
import sys
from importlib.metadata import entry_points

import matplotlib

matplotlib.use('Agg')  # before cli imports pyplot: never open windows during tests

import pytest

from bcsa_dcd import analysis, cli
from helpers import CUSTOM, write_config

GRAPH = CUSTOM / 'graph-1.csv'


@pytest.fixture
def shown(monkeypatch):
    """Count plt.show calls instead of opening windows."""
    calls = []
    monkeypatch.setattr(analysis.plt, 'show', lambda: calls.append(1))
    yield calls
    analysis.plt.close('all')


@pytest.fixture
def config(tmp_path):
    return lambda **overrides: write_config(tmp_path / 'config.toml', **overrides)


def run(*args):
    return cli.main([str(arg) for arg in args])


def rows(path):
    return path.read_text(encoding='utf-8').splitlines()[1:]  # without the header


@pytest.mark.parametrize('runs_flag, runs', [([], 1), (['--runs', 3], 3)])
def test_output_runs_and_no_plot(runs_flag, runs, tmp_path, config, shown):
    output = tmp_path / 'new' / 'results.csv'  # the folder does not exist yet
    run(
        GRAPH, '--mode', 'static', '--config', config(), '--output', output, '--no-plot', *runs_flag
    )
    assert len(rows(output)) == runs  # one run unless --runs says otherwise
    assert shown == []


def test_config_toml_is_the_default(tmp_path, monkeypatch, shown):
    write_config(tmp_path / 'config.toml')
    monkeypatch.chdir(tmp_path)
    run(GRAPH, '--mode', 'static', '--no-plot')
    assert len(rows(tmp_path / 'results.csv')) == 1


def test_same_seed_same_results(tmp_path, config, shown):
    for name in ['first.csv', 'second.csv']:
        run(
            CUSTOM,
            '--mode',
            'dynamic',
            '--config',
            config(),
            '--output',
            tmp_path / name,
            '--seed',
            7,
            '--no-plot',
        )
    assert (tmp_path / 'first.csv').read_bytes() == (tmp_path / 'second.csv').read_bytes()


def test_plot_dir_saves_instead_of_showing(tmp_path, config, shown):
    plots = tmp_path / 'plots'
    run(
        CUSTOM,
        '--mode',
        'dynamic',
        '--config',
        config(),
        '--output',
        tmp_path / 'r.csv',
        '--plot-dir',
        plots,
    )
    assert sorted(p.name for p in plots.iterdir()) == sorted(
        f'snapshot-{i}-{kind}.png' for i in (1, 2, 3) for kind in ('communities', 'convergence')
    )
    assert all(p.read_bytes().startswith(b'\x89PNG') for p in plots.iterdir())
    assert shown == []


@pytest.mark.parametrize(
    'flags, level', [([], logging.INFO), (['--verbose'], logging.DEBUG), (['-q'], logging.WARNING)]
)
def test_log_level(flags, level, tmp_path, config, shown):
    package_logger = logging.getLogger('bcsa_dcd')
    before = package_logger.level
    try:
        run(
            GRAPH,
            '--mode',
            'static',
            '--config',
            config(),
            '--output',
            tmp_path / 'r.csv',
            '--no-plot',
            *flags,
        )
        assert package_logger.level == level
    finally:
        package_logger.setLevel(before)


# Each case: the arguments (built from the tmp folder and a config writer), and a word
# the error message must contain.
BAD_INPUT = {
    'unknown mode': (
        lambda tmp, config: [GRAPH, '--mode', 'dinamic', '--config', config()],
        'invalid choice',
    ),
    'no mode': (lambda tmp, config: [GRAPH, '--config', config()], '--mode'),
    # gamma, not alpha: if the check broke, alpha = 1 would make the run never end.
    'parameter out of range': (
        lambda tmp, config: [GRAPH, '--mode', 'static', '--config', config(gamma=1.5)],
        'gamma',
    ),
    'nb_exec in the config': (
        lambda tmp, config: [GRAPH, '--mode', 'static', '--config', config(nb_exec=2)],
        '--runs',
    ),
    'runs = 0': (
        lambda tmp, config: [GRAPH, '--mode', 'static', '--config', config(), '--runs', 0],
        '--runs',
    ),
    'static on a folder': (
        lambda tmp, config: [CUSTOM, '--mode', 'static', '--config', config()],
        'graph file',
    ),
    'dynamic on a file': (
        lambda tmp, config: [GRAPH, '--mode', 'dynamic', '--config', config()],
        'folder',
    ),
    'missing network': (
        lambda tmp, config: [tmp / 'nope.csv', '--mode', 'static', '--config', config()],
        'graph file',
    ),
    'missing config': (
        lambda tmp, config: [GRAPH, '--mode', 'static', '--config', tmp / 'nope'],
        'config file',
    ),
    'no snapshots': (
        lambda tmp, config: [
            (tmp / 'empty').mkdir() or tmp / 'empty',
            '--mode',
            'dynamic',
            '--config',
            config(),
        ],
        'no graph*.csv',
    ),
    'no-plot and plot-dir': (
        lambda tmp, config: [
            GRAPH,
            '--mode',
            'static',
            '--config',
            config(),
            '--no-plot',
            '--plot-dir',
            tmp,
        ],
        'not allowed',
    ),
    'verbose and quiet': (
        lambda tmp, config: [GRAPH, '--mode', 'static', '--config', config(), '-v', '-q'],
        'not allowed',
    ),
}


@pytest.mark.parametrize('case', BAD_INPUT)
def test_bad_input_is_a_usage_error(case, tmp_path, config, monkeypatch, capsys, shown):
    args, message = BAD_INPUT[case]
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exit_:
        run(*args(tmp_path, config))
    assert exit_.value.code == 2
    assert message in capsys.readouterr().err
    assert not (tmp_path / 'results.csv').exists()  # stopped before writing anything


def test_console_script_runs_cli_main():
    (script,) = entry_points(group='console_scripts', name='bcsa-dcd')
    assert script.load() is cli.main


def test_python_m_runs_the_cli():
    done = subprocess.run(
        [sys.executable, '-m', 'bcsa_dcd', '--help'], capture_output=True, text=True, check=True
    )
    assert done.stdout.startswith('usage: bcsa-dcd')
