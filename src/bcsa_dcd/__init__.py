"""BCSA-DCD: artificial bee colony + simulated annealing for (dynamic) community detection."""

import logging

# A library leaves logging configuration to the application: without this, Python would
# print warnings and errors to stderr when no handler is configured.
logging.getLogger(__name__).addHandler(logging.NullHandler())
