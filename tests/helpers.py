"""Shared test helpers: graphs, random solutions and references independent of the app code."""

import json
from pathlib import Path

import networkx as nx

CUSTOM = Path(__file__).resolve().parent.parent / 'Datasets' / 'Dynamic' / 'Custom'

# A run small enough for about a second, large enough that every stage does some work.
# delta = 0.2 so that a move changes at least one gene on these 5-10 node graphs (with
# the default 0.05, int(10 * 0.05) = 0 genes change). sigma = 0.2 seeds 2 of the 10 food
# sources from CNM, so the elite path runs too.
CONFIG = {
    'nb_s': 10, 'nb_cycles': 5, 'limit_cycles': 2,
    'employed_bees_percentage': 0.5, 'T0': 1000, 'Tmin': 100, 'alpha': 0.6,
    'cycles_per_t': 2, 'gamma': 0.8, 'sigma': 0.2, 'delta': 0.2,
}


def toml_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, str):
        return json.dumps(value)  # a TOML basic string
    return repr(value)  # int, float, inf, nan


def write_config(path, **overrides):
    """Write CONFIG as TOML, with overrides (None leaves the key out); return the path as a string."""
    values = {**CONFIG, **overrides}
    path.write_text(''.join(f'{key} = {toml_value(value)}\n'
                            for key, value in values.items() if value is not None))
    return str(path)


def unweighted_karate():
    # networkx's karate club graph carries edge weights; the app's graphs never do.
    return nx.Graph(nx.karate_club_graph().edges())


def random_solution(g, rng):
    # Same construction as the app: each gene is a random neighbour of its node.
    return [rng.choice(list(g[i])) for i in range(g.number_of_nodes())]


def reference_communities(solution):
    """Union-find over the edges (i, solution[i]); independent of networkx."""
    parent = list(range(len(solution)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i, j in enumerate(solution):
        parent[find(i)] = find(j)
    groups = {}
    for i in range(len(solution)):
        groups.setdefault(find(i), set()).add(i)
    return {frozenset(g) for g in groups.values()}


def reference_labels(solution):
    """Label vector from reference_communities, independent of the app's node_labeling."""
    labels = [None] * len(solution)
    for label, community in enumerate(reference_communities(solution)):
        for node in community:
            labels[node] = label
    return labels
