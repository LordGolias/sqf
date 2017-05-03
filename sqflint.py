import sys
import argparse

from sqf.parser import parse
import sqf.analyser
from sqf.exceptions import SQFParserError


def analyze(code, writer=sys.stdout):
    try:
        result = parse(code)
    except SQFParserError as e:
        writer.write('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))
        return

    exceptions = sqf.analyser.analyze(result).exceptions
    for e in exceptions:
        writer.write('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))


def _main():
    parser = argparse.ArgumentParser(description="Static Analyser of SQF code")
    parser.add_argument('filename', nargs='?', type=argparse.FileType('r'), default=None,
                        help='The full path of the file to be analyzed')

    args = parser.parse_args()

    if args.filename is not None:
        with open(args.filename) as file:
            code = file.read()
    else:
        code = sys.stdin.read()

    analyze(code)


if __name__ == "__main__":
    _main()
