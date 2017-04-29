import sys

from sqf.parser import parse
from sqf.analyser import analyze
from sqf.scope_analyser import interpret
from sqf.exceptions import SQFParserError


def _main():
    text = sys.stdin.read()

    try:
        result = parse(text)
    except SQFParserError as e:
        sys.stdout.write('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))
        return

    exceptions = analyze(result)
    exceptions += interpret(result).exceptions
    for e in exceptions:
        sys.stdout.write('[%d,%d]:%s\n' % (e.position[0], e.position[1] - 1, e.message))


if __name__ == "__main__":
    _main()
