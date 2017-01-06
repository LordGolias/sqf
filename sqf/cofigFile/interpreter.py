from sqf.types import Code, Number, String, Variable, Array, Statement
from sqf.cofigFile.parser import parse, Keyword
from sqf.exceptions import SQFParserError


def _execute_array_tokens(tokens):
    result = []
    part = None
    first_comma_found = False
    for token in tokens:
        if token == Keyword(','):
            first_comma_found = True
            if part is None:
                raise SQFParserError('Array syntax is `[item1, item2, ...]`')
            assert(isinstance(part, (Number, String)))
            result.append(part)
            part = None
        else:
            assert(part is None)
            part = token

    # an empty array is a valid array
    if part is None and first_comma_found:
        raise SQFParserError('Array syntax is `[item1, item2, ...]`')
    result.append(part)

    return Array(result)


def execute_single(interpreter, global_vars, statement):
    assert(isinstance(interpreter, dict))
    base_tokens = statement.base_tokens

    if base_tokens and base_tokens[-1] == Keyword(';'):
        del base_tokens[-1]

    if len(base_tokens) == 0:
        return
    if len(base_tokens) == 3 and isinstance(base_tokens[0], Variable) and base_tokens[1] == Keyword('=') and \
        isinstance(base_tokens[2], (Number, String)):
        name = base_tokens[0].name
        value = base_tokens[2]
    elif len(base_tokens) == 3 and base_tokens[0] == Keyword('class') and isinstance(base_tokens[1], Variable) and \
        isinstance(base_tokens[2], Code):
        name = base_tokens[1].name
        value = _interpret(base_tokens[2], global_vars)
    elif len(base_tokens) == 4 and isinstance(base_tokens[0], Variable) and base_tokens[1] == Array([Statement([])]) and \
            base_tokens[2] == Keyword('=') and isinstance(base_tokens[3], Code):
        name = base_tokens[0].name
        value = _execute_array_tokens(base_tokens[3].base_tokens[0].base_tokens)
    elif len(base_tokens) == 2 and base_tokens[0] == Keyword('#define') and isinstance(base_tokens[1], Variable):
        name = base_tokens[1].name
        global_vars[name] = None
        return
    else:
        raise NotImplementedError(base_tokens, statement.position)

    interpreter[name] = value


def _interpret(statements, global_vars):
    result = {}

    for statement in statements:
        execute_single(result, global_vars, statement)

    return result


def interpret(script):
    statements = parse(script)
    global_vars = {}

    return _interpret(statements, global_vars)
