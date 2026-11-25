import math

import networkx as nx
from networkx.algorithms.community import modularity as nx_modularity
from scipy.stats import pearsonr
from sklearn.metrics.cluster import normalized_mutual_info_score


def modularity(snapshot, community_structure):
    # Unweighted Newman modularity; raises NotAPartition if communities overlap or miss nodes.
    return nx_modularity(snapshot, community_structure, weight=None)


def nmi(solution_a, solution_b):
    labels_a = node_labeling(solution_a)
    labels_b = node_labeling(solution_b)
    if len(labels_a) < len(labels_b):
        labels_b = labels_b[0 : len(labels_a)]
    return normalized_mutual_info_score(labels_a, labels_b)


def pearson_correlation(snapshot):

    r = []
    adjacency = nx.to_numpy_array(snapshot)
    for n in range(snapshot.number_of_nodes()):
        row = []
        for m in snapshot[n]:
            x = pearsonr(adjacency[n], adjacency[m])[0]
            row.append(1 / (1 + math.exp(-x)))
        r.append(row)
    return r


def locus_decode(solution):

    n = len(solution)
    g = nx.Graph()

    for i in range(n):
        g.add_edge(i, solution[i])

    return list(nx.connected_components(g))


def node_labeling(solution):

    labels = [0 for _ in range(len(solution))]
    partition = locus_decode(solution)

    for label, community in enumerate(partition):
        for member in community:
            labels[member] = label

    return labels
