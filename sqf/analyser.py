from sqf.exceptions import SQFParserError
from sqf.keywords import KeywordControl
from sqf.types import String, Statement, Code, Array, Boolean, Variable, Number, Keyword

constantTypes = (Array, Boolean, Variable, Number, Code, String, KeywordControl)


def is_invalid(t, tp1):
    return isinstance(t, constantTypes) and isinstance(tp1, constantTypes)

# Exceptions for constantTypes that can be next to each other
EXCEPTIONS = [
    lambda t,tp1: t == KeywordControl("from") and type(tp1) in (Number, Variable),
    lambda t,tp1: t == KeywordControl("for") and type(tp1) in (String, Variable),
    lambda t,tp1: t == KeywordControl("to") and type(tp1) in (Number, Variable),
    lambda t,tp1: t == KeywordControl("step") and type(tp1) in (Number, Variable),
    lambda t,tp1: t == KeywordControl("then") and type(tp1) in (Code, Variable),
    lambda t,tp1: t == KeywordControl("do") and type(tp1) in (Code, Variable),
    lambda t,tp1: t == KeywordControl("exitWith") and type(tp1) in (Code, Variable),
    lambda t,tp1: type(t) == Code and tp1 == KeywordControl("forEach"),
    lambda t,tp1: t == KeywordControl("forEach") and type(tp1) in [Array, Variable],
    lambda t,tp1: tp1 in [KeywordControl("to"), KeywordControl("from"), KeywordControl("do"), KeywordControl("step")],
    lambda t,tp1: t == KeywordControl("to") and type(tp1) in (Number, Variable),
    lambda t,tp1: t == KeywordControl("case"),
    lambda t,tp1: t == KeywordControl("else") and type(tp1) in (Code, Variable),
    lambda t,tp1: type(t) == Code and tp1 == KeywordControl("else"),
]


def check_statement(tokens, exceptions):
    if tokens[0] == Keyword("#define"):
        if len(tokens) == 1:
            exception = SQFParserError(tokens[0].position, "Syntax error: Wrong syntax for #define")
            exceptions.append(exception)
        return None

    for i, t in enumerate(tokens):
        if i != len(tokens) - 1:
            tp1 = tokens[i + 1]

            invalid = is_invalid(t,tp1)
            if invalid:
                for exception in EXCEPTIONS:
                    if exception(t, tp1):
                        invalid = False
                        break
                if invalid:
                    exception = SQFParserError(tp1.position, "Syntax error: '%s' can't preceed '%s' (missing ';'?)" % (t, tp1))
                    exceptions.append(exception)


def analyze(statement, exceptions=None):
    if exceptions is None:
        exceptions = []  # mutable can't be default argument

    if not statement.base_tokens:
        return exceptions

    tokens = statement.base_tokens

    for s in tokens:
        if isinstance(s, Statement):
            check_statement(s.base_tokens, exceptions)
            analyze(s, exceptions=exceptions)
        elif isinstance(s, Code):
            analyze(s, exceptions=exceptions)
        else:
            pass

    return exceptions
