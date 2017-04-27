import sys

from sqf.parser import parse
from sqf.exceptions import SQFParserError


def _main():
    # import argparse
    # parser = argparse.ArgumentParser(description='Parses a SQF file.')
    # parser.add_argument('script', metavar='script', type=str, nargs=1, help='The sqf script')

    # args = parser.parse_args()

    text = sys.stdin.read()
    print(repr(text))
    #text = "a \n{}}"

    try:
        parse(text)
    except SQFParserError as e:
        sys.stdout.write('[%d,%d]:%s\n' % (e.position[0], e.position[1], e.message))


if __name__ == "__main__":
    _main()
