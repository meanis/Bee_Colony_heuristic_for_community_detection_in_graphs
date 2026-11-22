from sklearn.metrics.cluster import normalized_mutual_info_score
from scipy.stats import pearsonr
import networkx as nx
from networkx.algorithms.community import modularity as nx_modularity
import math

def modularity(snapshot, community_structure):
    # Unweighted Newman modularity; raises NotAPartition if communities overlap or miss nodes.
    return nx_modularity(snapshot, community_structure, weight=None)

def NMI(A, B):
    A = node_labeling(A)
    B = node_labeling(B)
    if (len(A) < len(B)):
        B = B[0:len(A)]
    return normalized_mutual_info_score(A, B)

def pearson_correlation(snapshot):

    r = []
    A = nx.to_numpy_array(snapshot)
    for n in range(snapshot.number_of_nodes()):
        l = []
        for m in snapshot[n]:
            x = pearsonr(A[n], A[m])[0]
            l.append(1 / (1 + math.exp(-x)))
        r.append(l)
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

    label = 0
    for community in partition:
        for member in community:
            labels[member] = label
        label += 1

    return labels