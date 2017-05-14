import sys
import os
import argparse

from sqf.parser import parse
import sqf.analyzer
from sqf.exceptions import SQFParserError


class Writer:
    def __init__(self):
        self.strings = []

    def write(self, message):
        self.strings.append(message)


def analyze(code, writer=sys.stdout):
    try:
        result = parse(code)
    except SQFParserError as e:
        writer.write('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))
        return

    exceptions = sqf.analyzer.analyze(result).exceptions
    for e in exceptions:
        writer.write('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))


def analyze_dir(directory, writer):
    """
    Analyzes a directory recursively
    """
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".sqf"):
                file_path = os.path.join(root, file)

                writer_helper = Writer()

                with open(file_path) as f:
                    analyze(f.read(), writer_helper)

                if writer_helper.strings:
                    writer.write(os.path.relpath(file_path, directory) + '\n')
                    for string in writer_helper.strings:
                        writer.write('\t%s' % string)
    return writer


def readable_dir(prospective_dir):
    if not os.path.isdir(prospective_dir):
        raise Exception("readable_dir:{0} is not a valid path".format(prospective_dir))
    if os.access(prospective_dir, os.R_OK):
        return prospective_dir
    else:
        raise Exception("readable_dir:{0} is not a readable dir".format(prospective_dir))


def parse_args(args):
    parser = argparse.ArgumentParser(description="Static Analyzer of SQF code")
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'), default=None,
                        help='The full path of the file to be analyzed')
    parser.add_argument('-d', '--directory', nargs='?', type=readable_dir, default=None,
                        help='The full path of the directory to recursively analyse sqf files on')
    parser.add_argument('-o', '--output', nargs='?', type=argparse.FileType('w'), default=None,
                        help='File path to redirect the output to (default to stdout)')

    return parser.parse_args(args)


def main(args):
    args = parse_args(args)

    if args.output is None:
        writer = sys.stdout
    else:
        writer = args.output

    if args.file is None and args.directory is None:
        code = sys.stdin.read()
        analyze(code, writer)
    elif args.file is not None:
        code = args.file.read()
        args.file.close()
        analyze(code, writer)
    else:
        analyze_dir(args.directory, writer)

    if args.output is not None:
        writer.close()

def _main():
    main(sys.argv[1:])


if __name__ == "__main__":
    _main()
