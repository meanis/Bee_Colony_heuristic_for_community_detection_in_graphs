"""``python -m bcsa_dcd``: the same command line as the ``bcsa-dcd`` script."""

import sys

from .cli import main

if __name__ == '__main__':
    sys.exit(main())
