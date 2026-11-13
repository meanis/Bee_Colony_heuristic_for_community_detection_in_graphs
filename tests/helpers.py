"""Shared test helpers: graphs, random solutions and references independent of the app code."""

import networkx as nx


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
