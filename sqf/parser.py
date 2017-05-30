from collections import defaultdict
import re

import sqf.base_type
from sqf.base_tokenizer import tokenize

from sqf.exceptions import SQFParenthesisError, SQFParserError
from sqf.types import Statement, Code, Number, Boolean, Variable, Array, String, Keyword, Namespace, Preprocessor, ParserType
from sqf.keywords import KEYWORDS, NAMESPACES, PREPROCESSORS
from sqf.parser_types import Comment, Space, Tab, EndOfLine, BrokenEndOfLine, EndOfFile, ParserKeyword
from sqf.interpreter_types import DefineStatement, IncludeStatement, DefineResult, IfDefResult
from sqf.parser_exp import parse_exp


def rindex(the_list, value):
    return len(the_list) - the_list[::-1].index(value) - 1


def index(the_list, value):
    return the_list.index(value)


_LEVELS = {'[]': 0, '()': 0, '{}': 0, '#include': 0, '#define': 0, 'ifdef': 0, 'ifdef_open_close': 0}


STOP_KEYWORDS = {
    'single': (ParserKeyword(';'),),
    'both': (ParserKeyword(';'), ParserKeyword(',')),
}

OPEN_PARENTHESIS = (ParserKeyword('['), ParserKeyword('('), ParserKeyword('{'))
CLOSE_PARENTHESIS = (ParserKeyword(']'), ParserKeyword(')'), ParserKeyword('}'))
CLOSE_TO_OPEN = {
    '(': ')', ')': '(',
    '[': ']', ']': '[',
    '{': '}', '}': '{'
}
PARENTHESIS_STATES = {'[]', '()', '{}'}


def get_all_tokens(states):
    tokens = []
    for state in states:
        if state['state'] in PARENTHESIS_STATES:
            tokens.append(ParserKeyword(state['state'][0]))
        tokens += sqf.base_type.get_all_tokens(state['tokens'])
    return tokens


def get_coord(tokens):
    return sqf.base_type.get_coord(''.join([str(x) for x in tokens]))


def add_coords(coord1, tokens):
    coord2 = get_coord(tokens)
    return coord1[0] + coord2[0], coord1[1] + coord2[1] - 1


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
    if token in ('(', ')', '[', ']', '{', '}', ',', ';'):
        return ParserKeyword(token)
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


def replace_in_expression(expression, args, arg_indexes, remaining_tokens):
    """
    Recursively replaces matches of `args` in expression (a list of Types).
    """
    replacing_expression = []
    for token in expression:
        if isinstance(token, Statement):
            new_expression = replace_in_expression(token.content, args, arg_indexes, remaining_tokens)
            token = Statement(new_expression, ending=token.ending, parenthesis=token.parenthesis)
            replacing_expression.append(token)
        else:
            for arg, arg_index in zip(args, arg_indexes):
                if str(token) == arg:
                    replacing_expression.append(remaining_tokens[arg_index])
                    break
            else:
                replacing_expression.append(token)
    return replacing_expression


def get_new_remaining_tokens(define_expression, args, arg_indexes, remaining_tokens, i):
    replacing_expression = replace_in_expression(define_expression, args, arg_indexes, remaining_tokens)

    replacing_len = len(sqf.base_type.get_all_tokens(replacing_expression))
    arg_number = len(args)

    replaced_len = 1 + 2 * (arg_number != 0) + 2 * arg_number - 1 * (arg_number != 0)

    new_remaining_tokens = replacing_expression + remaining_tokens[i + replaced_len:]

    return new_remaining_tokens, replaced_len, replacing_len


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
            if token in ('\n', '\r\n'):
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


def is_end_statement(token, state):
    if state is None or state in PARENTHESIS_STATES:
        if state == '[]':
            stops = 'single'
        else:
            stops = 'both'
        return token in STOP_KEYWORDS[stops] or isinstance(token, EndOfFile)
    return isinstance(token, EndOfFile)


def statement_stops_at(all_tokens, states):
    state = states[-1]['state']
    for i, token in enumerate(all_tokens):
        if is_end_statement(token, state):
            return i
        if token in CLOSE_PARENTHESIS and (CLOSE_TO_OPEN[token.value] + token.value) == state:
            return i - 1

    return len(all_tokens) - 1  # EndOfFile is excluded


def get_ifdef_variable(tokens, ifdef_i, coord_until_here):
    variable = None
    eol_i = None
    for i, token in enumerate(tokens[ifdef_i:]):
        if type(token) == EndOfLine:
            eol_i = ifdef_i + i
            break
        if type(token) in (Variable, Keyword):
            variable = str(token)
    if variable is not None and eol_i is not None:
        return variable, eol_i
    raise SQFParserError(add_coords(coord_until_here, tokens[:ifdef_i]), '#ifdef statement must contain a variable')


def get_ifdef_tokens(tokens, defines, coord_until_here):
    try:
        ifdef_i = index(tokens, Preprocessor('#ifdef'))
        is_ifdef = True
    except ValueError:
        ifdef_i = index(tokens, Preprocessor('#ifndef'))
        is_ifdef = False
    try:
        else_i = rindex(tokens, Preprocessor('#else'))
    except ValueError:
        else_i = None
    endif_i = rindex(tokens, Preprocessor('#endif'))

    variable, eol_i = get_ifdef_variable(tokens, ifdef_i, coord_until_here)

    is_def = (variable in defines)

    replacing_expression = []
    if is_def and is_ifdef or not is_def and not is_ifdef:
        if else_i is None:
            to = endif_i
            replacing_expression = tokens[eol_i:to]
        else:
            to = else_i
            replacing_expression = tokens[eol_i:to]
    elif else_i is not None:
        replacing_expression = tokens[else_i + 1:endif_i]

    return replacing_expression


def is_last_endif(if_def_tokens):
    difference = 0
    for token in if_def_tokens:
        if token in (Preprocessor('#ifdef'), Preprocessor('#ifndef')):
            difference += 1
        if token == Preprocessor('#endif'):
            difference -= 1
    return difference == 1
assert is_last_endif([Preprocessor('#ifdef')])
assert (not is_last_endif([Preprocessor('#ifdef'), Preprocessor('#ifdef')]))
assert is_last_endif([Preprocessor('#ifdef'), Preprocessor('#ifdef'), Preprocessor('#endif')])


def parse_single(i, token, states, defines, remaining_tokens):
    print('parse_single', repr(token), states[-1]['state'])
    if states[-1]['state'] == 'ignore' and states[-1]['length']:
        token = None  # => do not add this token

    if states[-1]['state'] != 'ifdef' and token in (Preprocessor('#define'), Preprocessor('#include')):
        states.append({'state': 'preprocessor', 'tokens': []})
    elif states[-1]['state'] != 'ifdef' and token in (Preprocessor('#ifdef'), Preprocessor('#ifndef')):
        states.append({'state': 'ifdef', 'tokens': [], 'statements': []})
    elif states[-1]['state'] != 'preprocessor' and token in OPEN_PARENTHESIS:
        state_name = token.value + CLOSE_TO_OPEN[token.value]
        states.append({'state': state_name, 'tokens': [], 'statements': []})
        token = None

    elif states[-1]['state'] != 'ifdef' and \
         states[-1]['state'] != 'preprocessor' and str(token) in defines:  # is a define
        found, define_statement, arg_indexes = find_define_match(remaining_tokens, i, defines, token)

        if found:
            new_remaining_tokens, replaced_len, replacing_len = get_new_remaining_tokens(
                define_statement.expression, define_statement.args, arg_indexes, remaining_tokens, i)

            if new_remaining_tokens[-1] != EndOfFile():
                new_remaining_tokens.append(EndOfFile())
            j_sum = 0

            finished_with_tokens = False
            for j, token_j in enumerate(new_remaining_tokens):
                j_sum += len(sqf.base_type.get_all_tokens(Statement([token_j])))
                if str(token_j) in defines:
                    finished_with_tokens = True
                    print(repr(token_j))
                    break

                token = parse_single(j, token_j, states, defines, new_remaining_tokens)

                if is_end_statement(token, states[-1]['state']) or \
                        isinstance(token, (DefineStatement, IncludeStatement)):
                    tokens = states[-1]['tokens']
                    statements = states[-1]['statements']
                    if type(token) != EndOfFile:
                        tokens.append(token)
                    if tokens:
                        statements.append(_analyze_tokens(tokens))
                    break

                if token is not None and type(token) != EndOfFile:
                    states[-1]['tokens'].append(token)

            tokens = get_all_tokens(states)
            print('tokens', tokens)
            print('original', states[0].get('original', []))

            # the tokens collected so far from previous replacements of define
            modified = states[0].get('modified', [])
            print('modified', modified)
            # the tokens before
            tokens_before = tokens[:-j_sum + 1 - len(modified)]
            print('before', tokens_before)
            tokens_middle = remaining_tokens[i:i + replaced_len]
            tokens_after = tokens[len(tokens_before) + len(modified) + replacing_len:]
            states[0]['modified'] = states[0].get('modified', []) + tokens
            states[0]['original'] = states[0].get('original', []) + tokens_before + tokens_middle + tokens_after
            ignore_length = len(tokens_middle) + len(tokens_after)
            print(finished_with_tokens, states[0]['original'])

            if finished_with_tokens:
                states.append({'state': 'ignore', 'length': 2, 'tokens': []})
            else:
                # pick last statement and convert it to a DefineResult
                result = states[-1]['statements'][-1]

                states[-1]['statements'][-1] = DefineResult(states[0]['original'], result)
                del states[0]['original']
                del states[0]['modified']
                states[-1]['tokens'] = []

                # ignore the tokens used after this one
                states.append({'state': 'ignore', 'length': ignore_length, 'tokens': []})
                token = None

    if states[-1]['state'] == 'preprocessor' and type(token) in (EndOfLine, Comment, EndOfFile):
        if type(token) != EndOfFile:
            states[-1]['tokens'].append(token)

        tokens = states[-1]['tokens']
        if tokens[0] == Preprocessor('#define'):
            statement = _analyze_define(tokens)
            defines[statement.variable_name][len(statement.args)] = statement
        else:
            statement = IncludeStatement(tokens)

        del states[-1]
        # add the statement to the previous state
        token = statement
    if states[-1]['state'] == 'ifdef' and token == Preprocessor('#endif') and is_last_endif(states[-1]['tokens']):
        if type(token) != EndOfFile:
            states[-1]['tokens'].append(token)
        original_tokens = states[-1]['tokens'].copy()
        del states[-1]

        ifdef_tokens = get_ifdef_tokens(original_tokens, defines, get_coord(remaining_tokens[i:]))
        extra_tokens = ifdef_tokens[:]
        extra_tokens += remaining_tokens[i+1:]

        j_sum = 0
        states_len = len(states)
        states_offset = 0
        for j, token_j in enumerate(extra_tokens):
            j_sum += len(sqf.base_type.get_all_tokens(Statement([token_j])))
            token = parse_single(j, token_j, states, defines, extra_tokens)
            if states_len + states_offset < len(states):
                states_offset += 1
            elif states_len + states_offset > len(states):
                states_offset -= 1

            if is_end_statement(token, states[-1]['state']) or \
                    isinstance(token, (DefineStatement, IncludeStatement)):
                tokens = states[-1]['tokens']
                statements = states[-1]['statements']
                if type(token) != EndOfFile:
                    tokens.append(token)
                else:
                    j_sum -= 1
                if tokens:
                    statements.append(_analyze_tokens(tokens))
                states[-1]['tokens'] = []
                token = None
                if states_offset == -1 or len(states) == 1:
                    break

            if token is not None and type(token) != EndOfFile:
                states[-1]['tokens'].append(token)

        if states[-1]['statements']:
            result = states[-1]['statements'][-1]
        else:
            result = Statement([])

        tokens_before = result.get_all_tokens()[:-j_sum]
        tokens_middle = original_tokens
        tokens_after = result.get_all_tokens()[len(tokens_before) + len(ifdef_tokens):]

        original_tokens = tokens_before + tokens_middle + tokens_after

        ignore_length = len(tokens_after) + 1

        # ignore the tokens used after this one
        if states[-1]['statements']:
            states[-1]['statements'][-1] = IfDefResult(original_tokens, result)
        else:
            states[-1]['statements'].append(IfDefResult(original_tokens, result))
        states.append({'state': 'ignore', 'length': ignore_length, 'tokens': []})
        token = None

    if states[-1]['state'] != 'preprocessor' and token in CLOSE_PARENTHESIS:
        state_name = CLOSE_TO_OPEN[token.value] + token.value
        if states[-1]['state'] != state_name:
            raise SQFParenthesisError(
                get_coord(remaining_tokens[:i]),
                'Trying to close parenthesis without them opened.')
        state = states[-1]['state']
        tokens = states[-1]['tokens']
        statements = states[-1]['statements']
        if state == '()':
            if tokens:
                statements.append(_analyze_tokens(tokens))
            token = Statement(statements, parenthesis=True)
        elif state == '{}':
            if tokens:
                statements.append(_analyze_tokens(tokens))
            token = Code(statements)
        elif state == '[]':
            if statements:
                if isinstance(statements[0], DefineResult):
                    tokens = sqf.base_type.get_all_tokens(statements[0].result)
                    statements[0].result = Array(_analyze_array(tokens, _analyze_tokens, remaining_tokens[:i]))
                    statements[0]._tokens = [
                        Array(_analyze_array(statements[0]._tokens, _analyze_tokens, remaining_tokens[:i]))]
                    token = statements[0]
                else:
                    raise SQFParserError(get_coord(remaining_tokens[:i]),
                                         'A statement %s cannot be in an array' % Statement(statements))
            else:
                token = Array(_analyze_array(tokens, _analyze_tokens, remaining_tokens[:i]))
        else:
            assert False

        del states[-1]

    if states[-1]['state'] == 'ignore':
        states[-1]['length'] -= 1
        if states[-1]['length'] <= 0:
            del states[-1]

    return token


def parse_all(all_tokens, defines=None):
    if defines is None:
        defines = defaultdict(dict)
    states = [{
        'state': None,
        'tokens': [],
        'statements': []
    }]

    for i, token in enumerate(all_tokens):
        token = parse_single(i, token, states, defines, all_tokens)

        if is_end_statement(token, states[-1]['state']) or isinstance(token, (DefineStatement, IncludeStatement)):
            tokens = states[-1]['tokens']
            statements = states[-1]['statements']
            if type(token) != EndOfFile:
                tokens.append(token)
            if tokens:
                statements.append(_analyze_tokens(tokens))
            states[-1]['tokens'] = []
            token = None

        if token is not None and type(token) != EndOfFile:
            states[-1]['tokens'].append(token)

    if len(states) != 1:
        last_state = states[-1]['state']
        message = 'Parenthesis "%s" not closed' % last_state[0]
        if last_state == 'ifdef':
            message = '#ifdef statement not closed'

        start = len(all_tokens) - sum(len(sqf.base_type.get_all_tokens(x)) for x in states[-1]['statements'])
        raise SQFParenthesisError(get_coord(all_tokens[:start - 1]), message)

    return Statement(states[0]['statements']), defines


def _analyze_simple(tokens):
    return Statement(tokens)


def _analyze_tokens(tokens):
    ending = None
    if tokens and tokens[-1] in STOP_KEYWORDS['both']:
        ending = tokens[-1].value
        del tokens[-1]

    statement = parse_exp(tokens, container=Statement)
    if isinstance(statement, Statement):
        statement.ending = ending
    else:
        statement = Statement([statement], ending=ending)

    return statement


def _analyze_array(tokens, analyze_tokens, tokens_until):
    result = []
    part = []
    first_comma_found = False
    for token in tokens:
        if token == ParserKeyword(','):
            first_comma_found = True
            if not part:
                raise SQFParserError(get_coord(tokens_until), 'Array cannot have an empty element')
            result.append(analyze_tokens(part))
            part = []
        else:
            part.append(token)

    # an empty array is a valid array
    if part == [] and first_comma_found:
        raise SQFParserError(get_coord(tokens_until), 'Array cannot have an empty element')
    elif tokens:
        result.append(analyze_tokens(part))
    return result


def _analyze_define(tokens):
    # todo: pass coordinates of first token to this function to point exceptions
    assert(tokens[0] == Preprocessor('#define'))

    valid_indexes = [i for i in range(len(tokens))
                     if not isinstance(tokens[i], ParserType) or str(tokens[i]) in '(){}[]']
    parenthesis_indexes = [i for i in range(len(valid_indexes)) if str(tokens[valid_indexes[i]]) in '(){}[]']

    if len(valid_indexes) < 2:
        raise SQFParserError(get_coord(str(tokens[0])), '#define needs at least one argument')
    variable = str(tokens[valid_indexes[1]])
    if len(valid_indexes) == 2:
        return DefineStatement(tokens, variable)
    elif len(valid_indexes) >= 3 and valid_indexes[1] + 1 == valid_indexes[2] and tokens[valid_indexes[2]] == ParserKeyword('('):
        if len(parenthesis_indexes) == 1:
            raise SQFParserError(get_coord(str(tokens[0])), '#define argument parenthesis not closed')
        if tokens[valid_indexes[parenthesis_indexes[0]]] != ParserKeyword('(') or \
           tokens[valid_indexes[parenthesis_indexes[1]]] != ParserKeyword(')'):
            raise SQFParserError(get_coord(str(tokens[0])), '#define argument parenthesis incorrect')

        args_tokens = tokens[valid_indexes[parenthesis_indexes[0]]+1:valid_indexes[parenthesis_indexes[1]]]
        args_str = str(''.join(str(x) for x in args_tokens))
        if ' ' in args_str:
            raise SQFParserError(get_coord(str(tokens[0])), '#define arguments cannot contain spaces')

        args = args_str.split(',')
        remaining = tokens[valid_indexes[parenthesis_indexes[1]+1]:]
        return DefineStatement(tokens, variable, remaining, args=args)
    elif len(valid_indexes) >= 3:
        remaining = tokens[valid_indexes[2]:]
        return DefineStatement(tokens, variable, remaining)


def find_define_match(all_tokens, i, defines, token):
    found = False
    define_statement = None
    arg_indexes = []
    if i + 1 < len(all_tokens) and str(all_tokens[i + 1]) == '(':
        possible_args = defines[str(token)]
        arg_indexes = []
        for arg_number in possible_args:
            if arg_number == 0:
                continue

            for arg_i in range(arg_number + 1):
                if arg_i == arg_number:
                    index = i + 2 + 2 * arg_i - 1
                else:
                    index = i + 2 + 2 * arg_i

                if index >= len(all_tokens):
                    break
                arg_str = str(all_tokens[index])

                if arg_i == arg_number and arg_str != ')':
                    break
                elif not re.match('(.*?)', arg_str):
                    break
                if arg_i != arg_number:
                    arg_indexes.append(index)
            else:
                define_statement = defines[str(token)][arg_number]
                found = True
                break
    elif 0 in defines[str(token)]:
        define_statement = defines[str(token)][0]
        arg_indexes = []
        found = True

    return found, define_statement, arg_indexes


def parse(script):
    tokens = [identify_token(x) for x in parse_strings_and_comments(tokenize(script))]

    result = parse_all(tokens + [EndOfFile()])[0]

    result.set_position((1, 1))

    return result
