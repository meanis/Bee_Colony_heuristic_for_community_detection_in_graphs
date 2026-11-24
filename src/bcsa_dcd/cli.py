"""Command line: ``bcsa-dcd NETWORK --mode {static,dynamic} [options]`` (``--help`` for all)."""

import argparse
import csv
import logging
import random
from pathlib import Path

from . import analysis, config, read_network
from .detector import BCSADCD
from .write_results import write_results

logger = logging.getLogger(__name__)

PARAM_COLUMNS = list(config.PARAMETERS)


def positive_int(text):
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f'must be at least 1, got {value}')
    return value


def build_parser():
    parser = argparse.ArgumentParser(
        prog='bcsa-dcd',
        description='Detect communities in a static graph, or in each snapshot of a dynamic '
                    'graph, with an artificial bee colony and simulated annealing heuristic.')
    parser.add_argument(
        'network', type=Path,
        help='a graph file (static mode), or a folder of graph*.csv snapshot files (dynamic mode)')
    parser.add_argument('--mode', required=True, choices=['static', 'dynamic'],
                        help='one graph, or a sequence of snapshots')
    parser.add_argument('--config', type=Path, default=Path('config.toml'),
                        help='TOML parameter file (default: %(default)s)')
    parser.add_argument('--output', type=Path, default=Path('results.csv'),
                        help='results file, one row per run (default: %(default)s)')
    parser.add_argument('--runs', type=positive_int, default=1,
                        help='number of runs, one results row each (default: %(default)s)')
    parser.add_argument('--seed', type=int,
                        help='seed for the random number generator, to make runs reproducible')

    plots = parser.add_mutually_exclusive_group()
    plots.add_argument('--no-plot', action='store_true', help='draw no plots')
    plots.add_argument('--plot-dir', type=Path,
                       help='save the plots as PNG files in this folder instead of showing them')

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument('-v', '--verbose', action='store_true', help='also log debug messages')
    verbosity.add_argument('-q', '--quiet', action='store_true', help='log only warnings and errors')
    return parser


def configure_logging(verbose, quiet):
    # The level is set on the package logger only: the root logger stays at WARNING, so
    # --verbose does not turn on the debug messages of matplotlib and the other libraries.
    level = logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO
    logging.basicConfig(format='%(levelname)s %(name)s: %(message)s')
    logging.getLogger('bcsa_dcd').setLevel(level)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    configure_logging(args.verbose, args.quiet)

    # Check everything before running, so that a bad input never leaves a half-written
    # results file behind.
    if args.mode == 'static' and not args.network.is_file():
        parser.error(f'static mode needs a graph file: {args.network}')
    if args.mode == 'dynamic' and not args.network.is_dir():
        parser.error(f'dynamic mode needs a folder of snapshot files: {args.network}')
    if not args.config.is_file():
        parser.error(f'config file not found: {args.config}')

    try:
        params = config.load(args.config)
    except config.ConfigError as error:
        parser.error(f'{args.config}: {error}')

    if args.mode == 'static':
        snapshots = read_network.read_static_network(str(args.network))
    else:
        snapshots = read_network.read_dynamic_network(str(args.network))
        if not snapshots:
            parser.error(f'no graph*.csv snapshot files in {args.network}')

    if args.seed is not None:
        random.seed(args.seed)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as file:
        writer = csv.writer(file, lineterminator='\n')
        writer.writerow(PARAM_COLUMNS + [f'Modularité of snapshot {i}'
                                         for i in range(1, len(snapshots) + 1)])
        for run in range(1, args.runs + 1):
            logger.info('Run %d of %d', run, args.runs)
            partitions, analysis_data = BCSADCD(params, snapshots).execute()
            write_results(writer, params, analysis_data)
    logger.info('Results written to %s', args.output)

    # Only the last run is plotted (issue #8).
    if not args.no_plot:
        if args.plot_dir is not None:
            args.plot_dir.mkdir(parents=True, exist_ok=True)
        analysis.draw(snapshots, partitions, analysis_data, plot_dir=args.plot_dir)
    return 0
