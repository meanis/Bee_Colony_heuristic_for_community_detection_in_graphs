"""The baseline scripts in baselines/: they run on a graph file and print a modularity.

On Zachary's karate club the two deterministic baselines have well-known results: CNM
finds Q = 0.3807 (Clauset, Newman and Moore 2004), and the best level of the Girvan-Newman
hierarchy has Q = 0.4013 (Newman and Girvan 2004).
"""

import runpy
from pathlib import Path

import pytest

from helpers import unweighted_karate

BASELINES = Path(__file__).resolve().parent.parent / 'baselines'


@pytest.fixture
def karate_file(tmp_path):
    path = tmp_path / 'karate.csv'
    path.write_text(''.join(f'{u} {v}\n' for u, v in unweighted_karate().edges()))
    return str(path)


def run(script, *args, capsys):
    """Run baselines/<script>.py's main with args; return the modularity it returns."""
    main = runpy.run_path(str(BASELINES / f'{script}.py'))['main']
    q = main([str(arg) for arg in args])
    assert capsys.readouterr().out == ''  # the result is logged, never printed
    return q


def test_cnm_reports_the_modularity_of_its_partition(karate_file, capsys):
    # The old script re-encoded the partition as a locus solution, which split communities
    # and printed 0.3354 here.
    assert run('cnm', karate_file, capsys=capsys) == pytest.approx(0.3807, abs=1e-4)


def test_girvan_newman_reports_its_best_level(karate_file, capsys):
    assert run('girvan_newman', karate_file, capsys=capsys) == pytest.approx(0.4013, abs=1e-4)


def test_label_propagation_is_reproducible_with_a_seed(karate_file, capsys):
    first = run('label_propagation', karate_file, '--seed', 3, capsys=capsys)
    second = run('label_propagation', karate_file, '--seed', 3, capsys=capsys)
    assert first == second
    assert -0.5 <= first < 1


def test_label_propagation_finds_separate_triangles(tmp_path, capsys):
    # Whatever the seed, label propagation ends with one label per triangle (the only stable
    # state), and two equal disconnected parts have Q = 2 * (1/2 - (1/2)^2) = 1/2.
    path = tmp_path / 'triangles.csv'
    path.write_text('a b\nb c\nc a\nd e\ne f\nf d\n')
    for seed in range(5):
        assert run('label_propagation', path, '--seed', seed, capsys=capsys) == pytest.approx(0.5)


def test_only_the_three_scripts_remain():
    # The copies of functions.py and read_network.py are gone: the scripts use the package.
    assert sorted(p.name for p in BASELINES.glob('*.py')) == [
        'cnm.py', 'girvan_newman.py', 'label_propagation.py']
