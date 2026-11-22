"""Characterisation tests for read_static_network and read_dynamic_network.

File format: one edge per line, two node names separated by a single space. Names are
kept as strings and renumbered 0..n-1 in order of first appearance.
"""

from pathlib import Path

import pytest

import read_network

CUSTOM = Path(__file__).resolve().parent.parent / 'Datasets' / 'Dynamic' / 'Custom'


def edge_set(g):
    return {frozenset(e) for e in g.edges}


def reference_snapshots(texts):
    """Independent reader: ids by first appearance over all snapshots, nodes never removed.

    Returns one (nodes, edges) pair per snapshot text.
    """
    ids = {}
    result = []
    for text in texts:
        edges = set()
        for line in text.splitlines():
            u, v = line.split(' ')
            for name in (u, v):
                ids.setdefault(name, len(ids))
            edges.add(frozenset((ids[u], ids[v])))
        result.append((set(ids.values()), edges))
    return result


@pytest.fixture
def snapshot_dir(tmp_path, monkeypatch):
    """Write (name, text) files and fix the directory listing to that order.

    Real os.listdir order depends on the filesystem, so tests pin it.
    """
    def write(*files):
        for name, text in files:
            (tmp_path / name).write_text(text)
        names = [name for name, _ in files]
        monkeypatch.setattr(read_network, 'listdir', lambda folder: list(names))
        return str(tmp_path)  # the reader joins paths with '/', so it needs a str
    return write


def read_static(tmp_path, text):
    path = tmp_path / 'graph-1.csv'
    path.write_text(text)
    [g] = read_network.read_static_network(str(path))
    return g


def read_dynamic(tmp_path, text):
    (tmp_path / 'graph-1.csv').write_text(text)
    [g] = read_network.read_dynamic_network(str(tmp_path))
    return g


# The parsing code is duplicated in both readers, so the shared tests run on each.
READERS = [pytest.param(read_static, id='static'), pytest.param(read_dynamic, id='dynamic')]


# --- Both readers ----------------------------------------------------------------------

@pytest.mark.parametrize('read', READERS)
def test_numbering_by_first_appearance(tmp_path, read):
    # First appearance: 5 -> 0, 3 -> 1, 10 -> 2, 2 -> 3. Neither a string sort
    # ('10' < '2' < '3' < '5') nor a numeric sort (2 < 3 < 5 < 10) gives this.
    g = read(tmp_path, '5 3\n3 10\n10 5\n2 10\n')
    assert list(g.nodes) == [0, 1, 2, 3]
    assert edge_set(g) == {frozenset(e) for e in [(0, 1), (1, 2), (2, 0), (3, 2)]}


@pytest.mark.parametrize('read', READERS)
def test_repeated_and_reversed_edges_collapse(tmp_path, read):
    g = read(tmp_path, '0 1\n1 0\n0 1\n')
    assert g.number_of_nodes() == 2
    assert edge_set(g) == {frozenset((0, 1))}


# Current parsing quirks (issue #18). These pin today's behaviour; fixing #18 is a
# Phase 4 task that will update them.

@pytest.mark.parametrize('read', READERS)
def test_names_are_strings(tmp_path, read):
    # Non-numeric names work, and '01' and '1' are two different nodes.
    g = read(tmp_path, 'a b\n01 1\n')
    assert g.number_of_nodes() == 4
    assert edge_set(g) == {frozenset((0, 1)), frozenset((2, 3))}


@pytest.mark.parametrize('read', READERS)
def test_blank_line_raises(tmp_path, read):
    with pytest.raises(IndexError):
        read(tmp_path, '0 1\n\n1 2\n')


@pytest.mark.parametrize('read', READERS)
def test_tab_separated_raises(tmp_path, read):
    # The RDyn generator writes tab-separated files (issue #6).
    with pytest.raises(IndexError):
        read(tmp_path, '0\t1\n')


@pytest.mark.parametrize('read', READERS)
def test_double_space_misreads_edge(tmp_path, read):
    # '0  1' splits into ['0', '', '1']: the edge becomes '0'-'' and '1' is dropped.
    # Names: '0' -> 0, '' -> 1, '1' -> 2, '2' -> 3. A correct read would give 3 nodes.
    g = read(tmp_path, '0  1\n1 2\n')
    assert g.number_of_nodes() == 4
    assert edge_set(g) == {frozenset((0, 1)), frozenset((2, 3))}


# --- read_static_network ---------------------------------------------------------------

def test_static_custom_graph_matches_reference():
    path = CUSTOM / 'graph-1.csv'
    snapshots = read_network.read_static_network(str(path))
    [(nodes, edges)] = reference_snapshots([path.read_text()])
    assert len(snapshots) == 1
    assert set(snapshots[0].nodes) == nodes
    assert edge_set(snapshots[0]) == edges


# --- read_dynamic_network --------------------------------------------------------------

def test_dynamic_custom_dataset_matches_reference(monkeypatch):
    names = ['graph-1.csv', 'graph-2.csv', 'graph-3.csv']
    monkeypatch.setattr(read_network, 'listdir', lambda folder: list(names))
    snapshots = read_network.read_dynamic_network(str(CUSTOM))
    expected = reference_snapshots([(CUSTOM / name).read_text() for name in names])
    assert len(snapshots) == 3
    for g, (nodes, edges) in zip(snapshots, expected):
        assert set(g.nodes) == nodes
        assert edge_set(g) == edges


def test_edges_belong_to_their_snapshot(snapshot_dir):
    # Each snapshot holds only its own file's edges: earlier ones are removed, and
    # later ones do not leak back into earlier snapshots.
    folder = snapshot_dir(('graph-1.csv', '0 1\n1 2\n'), ('graph-2.csv', '2 3\n'))
    first, second = read_network.read_dynamic_network(folder)
    assert edge_set(first) == {frozenset((0, 1)), frozenset((1, 2))}
    assert edge_set(second) == {frozenset((2, 3))}


def test_nodes_persist_with_stable_ids(snapshot_dir):
    # Ids: 5 -> 0, 7 -> 1, 9 -> 2, then 3 -> 3. Node 3 is new in the second snapshot and
    # sorts before the others, so renumbering by sorted name would shift every id.
    folder = snapshot_dir(('graph-1.csv', '5 7\n7 9\n'), ('graph-2.csv', '9 3\n'))
    first, second = read_network.read_dynamic_network(folder)
    assert list(first.nodes) == [0, 1, 2]
    assert list(second.nodes) == [0, 1, 2, 3]  # 5 and 7 stay, now isolated
    assert edge_set(second) == {frozenset((2, 3))}


def test_empty_snapshot_keeps_all_nodes(snapshot_dir):
    folder = snapshot_dir(('graph-1.csv', '0 1\n1 2\n'), ('graph-2.csv', ''))
    _, second = read_network.read_dynamic_network(folder)
    assert list(second.nodes) == [0, 1, 2]
    assert second.number_of_edges() == 0


def test_file_filter(snapshot_dir):
    # Only names matching '^graph+.*.csv$' are read. Every other file holds an edge
    # that would add nodes if it were read.
    folder = snapshot_dir(
        ('graph-1.csv', '0 1\n'),
        ('graph-2.txt', 'txt1 txt2\n'),       # RDyn's output name (issue #6)
        ('notes.csv', 'n1 n2\n'),
        ('mygraph-3.csv', 'm1 m2\n'),
        ('graph-4.csv.bak', 'b1 b2\n'),
        ('README.md', 'r1 r2\n'),
        ('graph-5.csv', '1 2\n'),
    )
    snapshots = read_network.read_dynamic_network(folder)
    assert len(snapshots) == 2
    assert snapshots[1].number_of_nodes() == 3


def test_empty_folder(tmp_path):
    assert read_network.read_dynamic_network(str(tmp_path)) == []


@pytest.mark.xfail(strict=True, reason='issue #2: snapshots follow os.listdir order')
def test_dynamic_order_is_numeric(snapshot_dir):
    # graph-N.csv holds N edges (a star), so the edge counts identify the files.
    # A plain sorted() would give 1, 10, 2; only a numeric sort gives 1, 2, 10.
    def star(n):
        return ''.join(f'hub{n} leaf{n}.{i}\n' for i in range(n))

    folder = snapshot_dir(*[(f'graph-{n}.csv', star(n)) for n in (10, 2, 1)])
    snapshots = read_network.read_dynamic_network(folder)
    assert [g.number_of_edges() for g in snapshots] == [1, 2, 10]
