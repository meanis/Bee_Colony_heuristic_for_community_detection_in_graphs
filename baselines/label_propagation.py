"""Baseline: the modularity of the partition found by asynchronous label propagation.

Usage: uv run python baselines/label_propagation.py GRAPH [--seed N]
"""

import argparse
import logging

from networkx.algorithms.community import asyn_lpa_communities

from bcsa_dcd.functions import modularity
from bcsa_dcd.read_network import read_static_network

# Not __name__: that is '__main__' when the script runs.
logger = logging.getLogger('baselines.label_propagation')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('graph', help='graph file: one edge per line, two node names and a space')
    parser.add_argument(
        '--seed', type=int, help='seed for the label propagation order, to make runs reproducible'
    )
    args = parser.parse_args(argv)

    [g] = read_static_network(args.graph)
    q = modularity(g, asyn_lpa_communities(g, seed=args.seed))
    logger.info("modularité maximale détectée par l'algorithme de propagation d'étiquettes: %s", q)
    return q


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    main()
