import collections
import sys


def split(exp, op):
    # one is always found because of the condition used in parse_exp
    x = exp.partition(op)
    return x


def _partition(statement, keywords):
    for keyword in keywords:
        if keyword == statement:
            return keyword
        if keyword in statement:
            result = split(statement, keyword)
            return [_partition(i, keywords) for i in result]
    return statement


def flatten(l):
    for el in l:
        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def tokenize(statement):
    # the len=2 tokens have to be first!
    keywords = ('\\\n', '\r\n', '>>', '/*', '*/', '||', '//', '!=', '<=', '>=', '==', '"', "'", ' ', '=', ':', '{', '}',
                '(', ')', '[', ']', ';', ',', '!', '\n', '\t', '/', '*', '%', '^', '-', '+', '<', '>')

    # todo: do not use recursion to avoid setting this limit.
    old_value = sys.getrecursionlimit()
    sys.setrecursionlimit(20000)  # hard coded. Bad bad bad!
    result = list(flatten(_partition(statement, keywords)))
    sys.setrecursionlimit(old_value)

    return [token for token in result if token]
