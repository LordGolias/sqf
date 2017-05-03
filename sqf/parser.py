import sqf.base_type
from sqf.base_tokenizer import tokenize

from sqf.exceptions import SQFParenthesisError, SQFParserError
from sqf.types import Statement, Code, Number, Boolean, Variable, Array, String, Keyword, Namespace
from sqf.keywords import ORDERED_OPERATORS, KEYWORDS, NAMESPACES
from sqf.parser_types import Comment, Space, Tab, EndOfLine, BrokenEndOfLine
from sqf.parse_exp import parse_exp


def get_coord(tokens):
    return sqf.base_type.get_coord(''.join([str(x) for x in tokens]))


def identify_token(token):
    """
    The function that converts a token from tokenize to a BaseType.
    """
    if isinstance(token, Comment):
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
    if token.lower() in NAMESPACES:
        return Namespace(token)
    elif token.lower() in KEYWORDS:
        return Keyword(token)
    else:
        return Variable(token)


def parse_strings(all_tokens, identify_token):
    """
    Function that parses the strings of a script, transforming them into `String`.
    """
    string = ''
    tokens = []
    in_double = False
    string_mode = None  # [None, "single", "double"]

    for i, token in enumerate(all_tokens):
        if string_mode == "double":
            string += token
            if token == '"':
                if in_double:
                    in_double = False
                elif not in_double and i != len(all_tokens) - 1 and all_tokens[i+1] == '"':
                    in_double = True
                else:
                    tokens.append(String(string))
                    string_mode = None
                    in_double = False

        elif string_mode == "single":
            string += token
            if token == "'":
                if in_double:
                    in_double = False
                elif not in_double and i != len(all_tokens) - 1 and all_tokens[i + 1] == "'":
                    in_double = True
                else:
                    tokens.append(String(string))
                    string_mode = None
                    in_double = False
        else:  # string_mode is None:
            if token == '"':
                string = token
                string_mode = "double"
            elif token == "'":
                string = token
                string_mode = "single"
            else:
                tokens.append(identify_token(token))

    if string_mode is not None:
        raise SQFParserError(get_coord(tokens), 'String is not closed')

    return tokens


def parse_comments(all_tokens):
    tokens = []
    bulk_comment_mode = False
    line_comment_mode = False
    comment = ''
    for token in all_tokens:
        if token == '/*' and not line_comment_mode:
            bulk_comment_mode = True
        elif token == '//' and not bulk_comment_mode:
            line_comment_mode = True

        if token == '*/' and bulk_comment_mode:
            bulk_comment_mode = False
            tokens.append(Comment(comment + token))
            comment = ''
        elif token == '\n' and line_comment_mode:
            line_comment_mode = False
            tokens.append(Comment(comment + token))
            comment = ''
        elif bulk_comment_mode or line_comment_mode:
            comment += token
        else:
            tokens.append(token)

    if bulk_comment_mode or line_comment_mode:
        tokens.append(Comment(comment))

    return tokens


def _analyse_tokens(tokens):
    ending = ''
    if tokens and tokens[-1] in (Keyword(';'), Keyword(',')):
        ending = tokens[-1].value
        del tokens[-1]

    statement = parse_exp(tokens, ORDERED_OPERATORS, container=Statement, add_condition=
        lambda x: x or (isinstance(x, (Statement, Code)) and x.parenthesis is not None))
    if isinstance(statement, Statement):
        statement._ending = ending
    else:
        statement = Statement([statement], ending=ending)

    return statement


def _analyse_array_tokens(tokens, tokens_until):
    result = []
    part = []
    first_comma_found = False
    for token in tokens:
        if token == Keyword(','):
            first_comma_found = True
            if not part:
                raise SQFParserError(get_coord(tokens_until), 'Array cannot have an empty element')
            result.append(_analyse_tokens(part))
            part = []
        else:
            part.append(token)

    # an empty array is a valid array
    if part == [] and first_comma_found:
        raise SQFParserError(get_coord(tokens_until), 'Array cannot have an empty element')
    result.append(_analyse_tokens(part))

    return result


def parse_block(all_tokens, analyse_tokens, analyse_array, start=0, initial_lvls=None, stop_statement='both'):
    if not initial_lvls:
        initial_lvls = {'[]': 0, '()': 0, '{}': 0, '#define': 0, '#include': 0}
    lvls = initial_lvls.copy()

    statements = []
    tokens = []
    i = start

    while i < len(all_tokens):
        token = all_tokens[i]

        if token == Keyword('['):
            lvls['[]'] += 1
            expression, size = parse_block(all_tokens, analyse_tokens, analyse_array, i + 1, lvls, stop_statement='single')
            lvls['[]'] -= 1
            tokens.append(expression)
            i += size + 1
        elif token == Keyword('('):
            lvls['()'] += 1
            expression, size = parse_block(all_tokens, analyse_tokens, analyse_array, i + 1, lvls, stop_statement)
            lvls['()'] -= 1
            tokens.append(expression)
            i += size + 1
        elif token == Keyword('{'):
            lvls['{}'] += 1
            expression, size = parse_block(all_tokens, analyse_tokens, analyse_array, i + 1, lvls, stop_statement)
            lvls['{}'] -= 1
            tokens.append(expression)
            i += size + 1

        elif token == Keyword(']'):
            if lvls['[]'] == 0:
                raise SQFParenthesisError(get_coord(all_tokens[:i]), 'Trying to close right parenthesis without them opened.')

            if statements:
               raise SQFParserError(get_coord(all_tokens[:i]), 'A statement %s cannot be in an array' % Statement(statements))

            return Array(analyse_array(tokens, all_tokens[:i])), i - start
        elif token == Keyword(')'):
            if lvls['()'] == 0:
                raise SQFParenthesisError(get_coord(all_tokens[:i]), 'Trying to close parenthesis without opened parenthesis.')

            if tokens:
                statements.append(analyse_tokens(tokens))

            return Statement(statements, parenthesis=True), i - start
        elif token == Keyword('}'):
            if lvls['{}'] == 0:
                raise SQFParenthesisError(get_coord(all_tokens[:i]), 'Trying to close brackets without opened brackets.')

            if tokens:
                statements.append(analyse_tokens(tokens))

            return Code(statements), i - start
        elif stop_statement == 'both' and token in (Keyword(';'), Keyword(',')) or \
            stop_statement == 'single' and token == Keyword(';'):
            tokens.append(token)
            statements.append(analyse_tokens(tokens))
            tokens = []

        elif (token == Keyword('#define') and lvls['#define'] == 0) or \
                (token == Keyword('#include') and lvls['#include'] == 0):
            if tokens:
                # a pre-processor starts a new statement
                statements.append(analyse_tokens(tokens))
                tokens = []

            # repeat the loop for this token.
            lvls[token.value] += 1
            expression, size = parse_block(all_tokens, analyse_tokens, analyse_array, i, lvls, stop_statement)
            lvls[token.value] -= 1

            statements.append(expression)
            i += size - 1
        elif type(token) == EndOfLine and (lvls['#define'] != 0 or lvls['#include'] != 0):
            if tokens:
                statements.append(analyse_tokens(tokens))

            return Statement(statements), i - start
        else:
            tokens.append(token)
        i += 1

    for lvl_type in lvls:
        if lvls[lvl_type] != 0 and lvl_type not in ('#define', '#include'):
            raise SQFParenthesisError(get_coord(all_tokens[:start - 1]), 'Parenthesis "%s" not closed' % lvl_type[0])

    if tokens:
        statements.append(analyse_tokens(tokens))

    return Statement(statements), i - start


def parse(script):
    tokens = parse_strings(parse_comments(tokenize(script)), identify_token)

    result = parse_block(tokens, _analyse_tokens, _analyse_array_tokens)[0]

    result.set_position((1, 1))

    return result
