from os import listdir
import logging
import re
import csv
from copy import deepcopy

import networkx as nx

logger = logging.getLogger(__name__)

#########################################################################

def read_static_network(file_):

    snapshots = []

    with open(file_) as file:

        reader = csv.reader(file, delimiter=' ')

        g = nx.Graph()

        for line in reader:
            g.add_edge(line[0], line[1])
        g = nx.convert_node_labels_to_integers(g)

        logger.debug('Read %s: %s', file_, g)
        snapshots.append(g)

    return snapshots

#########################################################################

def read_dynamic_network(folder_):

    snapshots = []

    network_files = [file_ for file_ in listdir(folder_) if re.match('^graph+.*.csv$', file_)]
    g = nx.Graph()

    for file_ in network_files:

        g.remove_edges_from(list(g.edges))

        file = open(folder_ + '/' + file_)

        reader = csv.reader(file, delimiter=' ')

        for line in reader:
            g.add_edge(line[0], line[1])

        snapshots.append(deepcopy(g))

    snapshots = [nx.convert_node_labels_to_integers(g) for g in snapshots]

    return snapshots

#########################################################################