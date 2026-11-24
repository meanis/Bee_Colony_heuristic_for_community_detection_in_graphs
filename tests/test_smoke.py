"""Seeded end-to-end smoke tests: the whole pipeline runs and its output is well formed.

These check shapes and invariants, not exact values: they must keep passing when the
search changes, as long as it still produces valid results.
"""

import csv
import random

import matplotlib

matplotlib.use('Agg')  # before cli imports pyplot: never open windows during tests

import pytest

from bcsa_dcd import analysis, cli, config, functions, read_network
from bcsa_dcd.detector import BCSADCD
from helpers import CONFIG, CUSTOM, write_config

CUSTOM_FILES = ['graph-1.csv', 'graph-2.csv', 'graph-3.csv']
RUNS = 2
PARAM_COLUMNS = ['nb_s', 'nb_cycles', 'limit_cycles', 'employed_bees_percentage', 'T0',
                 'Tmin', 'alpha', 'cycles_per_t', 'gamma', 'sigma', 'delta']

# A dynamic graph that grows (f and g join in snapshot 2, h in snapshot 3) and leaves
# nodes isolated (d and e in snapshot 3). Custom keeps the same 10 nodes throughout, so
# it never exercises the code that extends solutions to new nodes.
GROWING = [
    ('graph-1.csv', 'a b\nb c\nc a\nd e\n'),
    ('graph-2.csv', 'a b\nb c\nc a\nd e\ne f\nf d\nf g\n'),
    ('graph-3.csv', 'a b\nb c\nc a\nf g\ng h\nh f\n'),
]


@pytest.fixture
def pin_listing(monkeypatch):
    """Fix the snapshot order to the given names (real listdir order varies, issue #2)."""
    def pin(names):
        monkeypatch.setattr(read_network, 'listdir', lambda folder: list(names))
    return pin


@pytest.fixture
def custom_dir(pin_listing):
    pin_listing(CUSTOM_FILES)
    return str(CUSTOM)


@pytest.fixture
def growing_dir(tmp_path, pin_listing):
    folder = tmp_path / 'growing'
    folder.mkdir()
    for name, text in GROWING:
        (folder / name).write_text(text)
    pin_listing([name for name, _ in GROWING])
    return str(folder)


def params():
    return config.validate(CONFIG)  # typed, as the CLI loads them


def run(snapshots, seed):
    random.seed(seed)
    return BCSADCD(params(), snapshots).execute()


def assert_valid_result(snapshots, partitions, analysis_data):
    gamma = CONFIG['gamma']
    assert len(partitions) == len(analysis_data) == len(snapshots)
    for g, fs, data in zip(snapshots, partitions, analysis_data):
        # A locus-based solution: one gene per node, pointing to a neighbour, or to the
        # node itself when it is isolated.
        assert len(fs.solution) == g.number_of_nodes()
        for node, gene in enumerate(fs.solution):
            assert gene in g[node] or (gene == node and g.degree(node) == 0)

        # Objective = gamma * Q + (1 - gamma) * NMI, with Q in [-1/2, 1) and NMI in [0, 1].
        # Recomputing Q from the solution isolates the NMI term, which must be in range.
        q = functions.modularity(g, functions.locus_decode(fs.solution))
        nmi_term = fs.cost - gamma * q
        assert -1e-12 <= nmi_term <= (1 - gamma) + 1e-12
        assert -gamma / 2 <= fs.cost <= 1

        # Convergence history: one entry per cycle, never decreasing, ending at the result.
        history = data['global_optimal']
        assert len(history) == CONFIG['nb_cycles']
        assert all(a <= b for a, b in zip(history, history[1:]))
        assert history[-1] == fs.cost


def test_static_run():
    snapshots = read_network.read_static_network(str(CUSTOM / 'graph-1.csv'))
    assert_valid_result(snapshots, *run(snapshots, seed=0))


@pytest.mark.parametrize('dataset', ['custom_dir', 'growing_dir'])
def test_dynamic_run(dataset, request):
    snapshots = read_network.read_dynamic_network(request.getfixturevalue(dataset))
    assert_valid_result(snapshots, *run(snapshots, seed=0))


def test_same_seed_same_result(custom_dir):
    snapshots = read_network.read_dynamic_network(custom_dir)
    first, second = run(snapshots, seed=7), run(snapshots, seed=7)
    assert [fs.solution for fs in first[0]] == [fs.solution for fs in second[0]]
    assert first[1] == second[1]  # the whole convergence history


@pytest.mark.parametrize('mode', ['static', 'dynamic'])
def test_cli_writes_results_and_plots(mode, custom_dir, tmp_path, monkeypatch, capsys):
    config_file = write_config(tmp_path / 'config.toml')
    path = str(CUSTOM / 'graph-1.csv') if mode == 'static' else custom_dir
    n_snapshots = 1 if mode == 'static' else 3

    runs = []  # each execution's (partitions, analysis_data), to compare with the CSV

    class RecordingRun(BCSADCD):
        def execute(self):
            runs.append(super().execute())
            return runs[-1]

    monkeypatch.setattr(cli, 'BCSADCD', RecordingRun)
    shown = []
    monkeypatch.setattr(analysis.plt, 'show', lambda: shown.append(1))
    monkeypatch.chdir(tmp_path)  # results.csv goes to the working directory by default
    try:
        assert cli.main([path, '--mode', mode, '--config', config_file, '--seed', '0',
                         '--runs', str(RUNS)]) == 0
    finally:
        analysis.plt.close('all')

    with open(tmp_path / 'results.csv', newline='') as file:
        header, *rows = list(csv.reader(file))
    assert header == PARAM_COLUMNS + [f'Modularité of snapshot {i}'
                                      for i in range(1, n_snapshots + 1)]
    assert len(rows) == len(runs) == RUNS
    for row, (partitions, _) in zip(rows, runs):
        assert [float(v) for v in row[:len(PARAM_COLUMNS)]] == [CONFIG[k] for k in PARAM_COLUMNS]
        # Each snapshot column is that run's final objective (not pure modularity,
        # despite the header: issue #3). str(float) round-trips exactly.
        assert [float(v) for v in row[len(PARAM_COLUMNS):]] == [fs.cost for fs in partitions]
    assert len(shown) == 2 * n_snapshots  # a community drawing and a convergence chart each

    assert capsys.readouterr().out == ''  # progress goes to logging, never to print
