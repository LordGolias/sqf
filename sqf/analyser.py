from sqf.exceptions import SQFParserError
from sqf.types import String, Statement, Code, Array, Boolean, Variable as V, Number as N

constantTypes = (Array, Boolean, V, N, Code, String)


def check_statement(tokens, exceptions):
    for i, t in enumerate(tokens):
        if i != len(tokens) - 1 and \
                isinstance(t, constantTypes) and isinstance(tokens[i+1], constantTypes):
            exception = SQFParserError(tokens[i + 1].position, "Syntax error: '%s' can't operate on '%s' (missing ';'?)" % (t, tokens[i + 1]))
            exceptions.append(exception)


def analyze(statement, exceptions=None):
    if exceptions is None:
        exceptions = []  # mutable can't be default argument
    for s in statement.base_tokens:
        if isinstance(s, Statement):
            check_statement(s.base_tokens, exceptions)
            analyze(s, exceptions)
        elif isinstance(s, Code):
            analyze(s, exceptions)
        else:
            pass

    return exceptions
