import sys
import csv
import logging

from .detector import BCSADCD
from . import read_configuration
from . import read_network
from .write_results import write_results
from . import analysis as anal

logger = logging.getLogger('bcsa_dcd.main')  # not __name__: that is '__main__' under python -m

def main(argv):

    params = read_configuration.read(argv[1])

    if argv[2] == 'static':
        snapshots = read_network.read_static_network(argv[3])
    elif argv[2] == 'dynamic':
        snapshots = read_network.read_dynamic_network(argv[3])

    with open('results.csv', 'w') as _file:
        writer = csv.writer(_file, lineterminator = '\n')
        writer.writerow([
            'nb_s',
            'nb_cycles',
            'limit_cycles',
            'employed_bees_percentage',
            'T0',
            'Tmin',
            'alpha',
            'cycles_per_t',
            'gamma',
            'sigma',
            'delta',
            ] + [
                f"Modularité of snapshot {i+1}" for i,v in enumerate(snapshots)
            ])

        nb_exec = int(params['nb_exec'])
        for execution in range(1, nb_exec + 1):
            logger.info('Execution %d of %d', execution, nb_exec)
            mobcsa_dcd_ = BCSADCD(params, snapshots)
            partitions, analysis_data = mobcsa_dcd_.execute()
            write_results(writer, params, analysis_data)

    anal.draw(snapshots, partitions, analysis_data)

if __name__ == '__main__':
    # Temporary: the CLI task replaces this with --verbose / --quiet.
    logging.basicConfig(level=logging.INFO, format='%(levelname)s %(name)s: %(message)s')
    sys.exit(main(sys.argv))