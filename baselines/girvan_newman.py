"""Baseline: the best modularity over the levels of the Girvan-Newman hierarchy.

Usage: uv run python baselines/girvan_newman.py GRAPH
"""

import argparse
import logging

from networkx.algorithms.community import girvan_newman

from bcsa_dcd.functions import modularity
from bcsa_dcd.read_network import read_static_network

# Not __name__: that is '__main__' when the script runs.
logger = logging.getLogger('baselines.girvan_newman')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('graph', help='graph file: one edge per line, two node names and a space')
    args = parser.parse_args(argv)

    [g] = read_static_network(args.graph)
    q = max(modularity(g, level) for level in girvan_newman(g))
    logger.info('modularité maximale détectée par Girvan et Newman: %s', q)
    return q


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    main()
