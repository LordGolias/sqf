from sqf.exceptions import SQFParserError
from sqf.keywords import KeywordControl
from sqf.types import String, Statement, Code, Array, Boolean, Variable, Number, Keyword

constantTypes = (Array, Boolean, Variable, Number, Code, String, KeywordControl, Statement)
switchTypes = (Array, Boolean, Variable, Number, String, Statement)


def first_base_token(statement):
    if not isinstance(statement, Statement):
        return statement
    assert (len(statement.base_tokens) > 0)
    token = statement.base_tokens[0]

    if isinstance(token, Statement):
        return first_base_token(token)
    else:
        return token


def is_invalid(t, tp1):
    return isinstance(t, constantTypes) and isinstance(tp1, constantTypes)

# Exceptions for constantTypes that can be next to each other
EXCEPTIONS = [
    lambda t,tp1: type(t) == Variable and t.is_global and type(tp1) in (Number, Statement, Variable),
    lambda t,tp1: t == KeywordControl("from") and type(tp1) in (Number, Statement, Variable),
    lambda t,tp1: t == KeywordControl("for") and type(tp1) in (String, Statement, Variable),
    lambda t,tp1: t == KeywordControl("if") and type(tp1) in (Statement,),
    lambda t,tp1: t == KeywordControl("switch") and type(tp1) in switchTypes,
    lambda t,tp1: t == KeywordControl("exitWith") and type(tp1) in (Code, Statement, Variable),
    lambda t,tp1: t == KeywordControl("then") and type(tp1) in (Code, Statement, Variable),
    lambda t,tp1: t == KeywordControl("to") and type(tp1) in (Number, Statement, Variable),
    lambda t,tp1: t == KeywordControl("step") and type(tp1) in (Number, Statement, Variable),
    lambda t,tp1: t == KeywordControl("then") and type(tp1) in (Code, Statement, Variable),
    lambda t,tp1: t == KeywordControl("do") and type(tp1) in (Code, Statement, Variable),
    lambda t,tp1: t == KeywordControl("exitWith") and type(tp1) in (Code, Statement, Variable),
    lambda t,tp1: type(t) == Code and tp1 == KeywordControl("forEach"),
    lambda t,tp1: t == KeywordControl("forEach") and type(tp1) in [Array, Statement, Variable],
    lambda t,tp1: tp1 in [KeywordControl('exitWith'), KeywordControl("then"), KeywordControl("to"), KeywordControl("from"), KeywordControl("do"), KeywordControl("step"), KeywordControl("else")],
    lambda t,tp1: t == KeywordControl("to") and type(tp1) in (Number, Statement, Variable),
    lambda t,tp1: t == KeywordControl("case"),
    lambda t,tp1: t == KeywordControl("else") and type(tp1) in (Code, Statement, Variable),
    lambda t,tp1: type(t) == Code and tp1 == KeywordControl("else"),
]


def check_statement(tokens, exceptions):
    if len(tokens) == 0:
        return

    if tokens[0] == Keyword("#define"):
        if len(tokens) == 1:
            exception = SQFParserError(tokens[0].position, "Wrong syntax for #define")
            exceptions.append(exception)
        return
    if tokens[0] == Keyword("#include"):
        if len(tokens) != 2 or type(tokens[1]) != String:
            exception = SQFParserError(tokens[0].position, "Wrong syntax for #include")
            exceptions.append(exception)
        return
    if tokens[0] == KeywordControl('case'):
        if len(tokens) > 2 and tokens[2] != Keyword(":"):
            exception = SQFParserError(tokens[2].position, "'case' 3rd part must be ':'")
            exceptions.append(exception)
        if len(tokens) > 3 and type(tokens[3]) != Code:
            exception = SQFParserError(tokens[3].position, "'case' 4th part must be code")
            exceptions.append(exception)
        if len(tokens) != 4:
            exception = SQFParserError(tokens[0].position, "'case' is a 4-part clause")
            exceptions.append(exception)
        return

    for i, t in enumerate(tokens):
        if i != len(tokens) - 1:
            tp1 = tokens[i + 1]

            if t in (KeywordControl('default'), KeywordControl('while')):
                if type(first_base_token(tp1)) != Code:
                    exception = SQFParserError(tp1.position,
                                               "'%s' must be followed by a code statement" % t.value)
                    exceptions.append(exception)
                continue

            invalid = is_invalid(t,tp1)
            if invalid:
                for exception in EXCEPTIONS:
                    if exception(t, tp1):
                        invalid = False
                        break
                if invalid:
                    exception = SQFParserError(tp1.position, "'%s' can't preceed '%s' (missing ';'?)" % (t, tp1))
                    exceptions.append(exception)


def analyze(statement, exceptions=None):
    if exceptions is None:
        exceptions = []  # mutable can't be default argument

    tokens = statement.base_tokens

    for s in tokens:
        if isinstance(s, Statement):
            check_statement(s.base_tokens, exceptions)
            analyze(s, exceptions=exceptions)
        elif isinstance(s, Array):
            for s_s in s.value:
                check_statement(s_s.base_tokens, exceptions)
                analyze(s_s, exceptions)
        elif isinstance(s, Code):
            analyze(s, exceptions=exceptions)

    return exceptions
