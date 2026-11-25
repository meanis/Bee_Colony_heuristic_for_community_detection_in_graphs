"""Baseline: the modularity of the partition found by CNM (Clauset-Newman-Moore greedy).

Usage: uv run python baselines/cnm.py GRAPH
"""

import argparse
import logging

from networkx.algorithms.community import greedy_modularity_communities

from bcsa_dcd.functions import modularity
from bcsa_dcd.read_network import read_static_network

# Not __name__: that is '__main__' when the script runs.
logger = logging.getLogger('baselines.cnm')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('graph', help='graph file: one edge per line, two node names and a space')
    args = parser.parse_args(argv)

    [g] = read_static_network(args.graph)
    q = modularity(g, greedy_modularity_communities(g))
    logger.info('modularité maximale détectée par CNM: %s', q)
    return q


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    main()
