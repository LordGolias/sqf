import sqf.base_type
from sqf.base_tokenizer import tokenize

from sqf.exceptions import SQFParenthesisError, SQFParserError
from sqf.types import Statement, Code, Number, Boolean, Variable, Array, String, Keyword, Namespace, Preprocessor
from sqf.keywords import KEYWORDS, NAMESPACES, PREPROCESSORS
from sqf.parser_types import Comment, Space, Tab, EndOfLine, BrokenEndOfLine
from sqf.parser_exp import parse_exp


def get_coord(tokens):
    return sqf.base_type.get_coord(''.join([str(x) for x in tokens]))


def identify_token(token):
    """
    The function that converts a token from tokenize to a BaseType.
    """
    if isinstance(token, (Comment, String)):
        return token
    if token == ' ':
        return Space()
    if token == '\t':
        return Tab()
    if token == '\\\n':
        return BrokenEndOfLine()
    if token in ('\n', '\r\n'):
        return EndOfLine(token)
    if token in ('true', 'false'):
        return Boolean(token == 'true')
    try:
        return Number(int(token))
    except ValueError:
        pass
    try:
        return Number(float(token))
    except ValueError:
        pass
    if token in PREPROCESSORS:
        return Preprocessor(token)
    if token.lower() in NAMESPACES:
        return Namespace(token)
    elif token.lower() in KEYWORDS:
        return Keyword(token)
    else:
        return Variable(token)


def parse_strings_and_comments(all_tokens):
    """
    Function that parses the strings of a script, transforming them into `String`.
    """
    string = ''  # the buffer for the activated mode
    tokens = []  # the final result
    in_double = False
    mode = None  # [None, "string_single", "string_double", "comment_line", "comment_bulk"]

    for i, token in enumerate(all_tokens):
        if mode == "string_double":
            string += token
            if token == '"':
                if in_double:
                    in_double = False
                elif not in_double and i != len(all_tokens) - 1 and all_tokens[i+1] == '"':
                    in_double = True
                else:
                    tokens.append(String(string))
                    mode = None
                    in_double = False
        elif mode == "string_single":
            string += token
            if token == "'":
                if in_double:
                    in_double = False
                elif not in_double and i != len(all_tokens) - 1 and all_tokens[i + 1] == "'":
                    in_double = True
                else:
                    tokens.append(String(string))
                    mode = None
                    in_double = False
        elif mode == "comment_bulk":
            string += token
            if token == '*/':
                mode = None
                tokens.append(Comment(string))
                string = ''
        elif mode == "comment_line":
            string += token
            if token == '\n':
                mode = None
                tokens.append(Comment(string))
                string = ''
        else:  # mode is None
            if token == '"':
                string = token
                mode = "string_double"
            elif token == "'":
                string = token
                mode = "string_single"
            elif token == '/*':
                string = token
                mode = "comment_bulk"
            elif token == '//':
                string = token
                mode = "comment_line"
            else:
                tokens.append(token)

    if mode in ("comment_line", "comment_bulk"):
        tokens.append(Comment(string))
    elif mode is not None:
        raise SQFParserError(get_coord(tokens), 'String is not closed')

    return tokens


def _analyze_tokens(tokens):
    ending = ''
    if tokens and tokens[-1] in (Keyword(';'), Keyword(',')):
        ending = tokens[-1].value
        del tokens[-1]

    statement = parse_exp(tokens, container=Statement)
    if isinstance(statement, Statement):
        statement._ending = ending
    else:
        statement = Statement([statement], ending=ending)

    return statement


def _analyze_array_tokens(tokens, tokens_until):
    result = []
    part = []
    first_comma_found = False
    for token in tokens:
        if token == Keyword(','):
            first_comma_found = True
            if not part:
                raise SQFParserError(get_coord(tokens_until), 'Array cannot have an empty element')
            result.append(_analyze_tokens(part))
            part = []
        else:
            part.append(token)

    # an empty array is a valid array
    if part == [] and first_comma_found:
        raise SQFParserError(get_coord(tokens_until), 'Array cannot have an empty element')
    elif tokens:
        result.append(_analyze_tokens(part))
    return result


def parse_block(all_tokens, analyze_tokens, analyze_array, start=0, initial_lvls=None, stop_statement='both'):
    if not initial_lvls:
        initial_lvls = {'[]': 0, '()': 0, '{}': 0}
        initial_lvls.update({x: 0 for x in PREPROCESSORS})
    lvls = initial_lvls.copy()

    statements = []
    tokens = []
    i = start

    while i < len(all_tokens):
        token = all_tokens[i]

        if token == Keyword('['):
            lvls['[]'] += 1
            expression, size = parse_block(all_tokens, analyze_tokens, analyze_array, i + 1, lvls, stop_statement='single')
            lvls['[]'] -= 1
            tokens.append(expression)
            i += size + 1
        elif token == Keyword('('):
            lvls['()'] += 1
            expression, size = parse_block(all_tokens, analyze_tokens, analyze_array, i + 1, lvls, stop_statement)
            lvls['()'] -= 1
            tokens.append(expression)
            i += size + 1
        elif token == Keyword('{'):
            lvls['{}'] += 1
            expression, size = parse_block(all_tokens, analyze_tokens, analyze_array, i + 1, lvls, stop_statement)
            lvls['{}'] -= 1
            tokens.append(expression)
            i += size + 1

        elif token == Keyword(']'):
            if lvls['[]'] == 0:
                raise SQFParenthesisError(get_coord(all_tokens[:i]), 'Trying to close right parenthesis without them opened.')

            if statements:
               raise SQFParserError(get_coord(all_tokens[:i]), 'A statement %s cannot be in an array' % Statement(statements))

            return Array(analyze_array(tokens, all_tokens[:i])), i - start
        elif token == Keyword(')'):
            if lvls['()'] == 0:
                raise SQFParenthesisError(get_coord(all_tokens[:i]), 'Trying to close parenthesis without opened parenthesis.')

            if tokens:
                statements.append(analyze_tokens(tokens))

            return Statement(statements, parenthesis=True), i - start
        elif token == Keyword('}'):
            if lvls['{}'] == 0:
                raise SQFParenthesisError(get_coord(all_tokens[:i]), 'Trying to close brackets without opened brackets.')

            if tokens:
                statements.append(analyze_tokens(tokens))

            return Code(statements), i - start
        elif stop_statement == 'both' and token in (Keyword(';'), Keyword(',')) or \
            stop_statement == 'single' and token == Keyword(';'):
            tokens.append(token)
            statements.append(analyze_tokens(tokens))
            tokens = []
        elif isinstance(token, Keyword) and token.value in PREPROCESSORS and lvls[token.value] == 0:
            if tokens:
                # a pre-processor starts a new statement
                statements.append(analyze_tokens(tokens))
                tokens = []

            # repeat the loop for this token.
            lvls[token.value] += 1
            expression, size = parse_block(all_tokens, analyze_tokens, analyze_array, i, lvls, stop_statement)
            lvls[token.value] -= 1

            statements.append(expression)
            i += size - 1
        elif type(token) == EndOfLine and any(lvls[x] != 0 for x in PREPROCESSORS):
            if tokens:
                if tokens[0] == Preprocessor('#define'):
                    statements.append(Statement(tokens))
                else:
                    statements.append(analyze_tokens(tokens))

            return Statement(statements), i - start
        else:
            tokens.append(token)
        i += 1

    for lvl_type in lvls:
        if lvls[lvl_type] != 0 and lvl_type not in PREPROCESSORS:
            raise SQFParenthesisError(get_coord(all_tokens[:start - 1]), 'Parenthesis "%s" not closed' % lvl_type[0])

    if tokens:
        statements.append(analyze_tokens(tokens))

    return Statement(statements), i - start


def parse(script):
    tokens = [identify_token(x) for x in parse_strings_and_comments(tokenize(script))]

    result = parse_block(tokens, _analyze_tokens, _analyze_array_tokens)[0]

    result.set_position((1, 1))

    return result
