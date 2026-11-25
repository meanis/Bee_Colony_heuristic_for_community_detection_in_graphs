import sys

from rdyn import RDyn


def main(argv):

    gen = RDyn(size=200, iterations=200, avg_deg=4, sigma=0.8)
    gen.execute(simplified=True)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
