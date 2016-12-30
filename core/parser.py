from core.base_tokenizer import tokenize

from core.exceptions import UnbalancedParenthesisSyntaxError, SyntaxError
from core.types import Statement, Code, Number, Boolean, Variable, Array, String, RESERVED_MAPPING, \
    RParenthesisOpen, RParenthesisClose, ParenthesisOpen, ParenthesisClose, BracketOpen, BracketClose, EndOfStatement, \
    Comma
from core.operators import OPERATORS, ORDERED_OPERATORS
from core.parse_exp import parse_exp


def identify_token(token):
    if token in OPERATORS:
        return OPERATORS[token]
    elif token in RESERVED_MAPPING:
        return RESERVED_MAPPING[token]
    elif token in ('true', 'false'):
        return Boolean(token == 'true')
    else:
        try:
            return Number(int(token))
        except ValueError:
            try:
                return Number(float(token))
            except ValueError:
                return Variable(token)


def parse_strings(all_tokens):
    tokens = []
    string_mode = False
    string = ''
    for i, token in enumerate(all_tokens):
        if token == '"':
            if string_mode:
                tokens.append(String(string))
                string = ''
                string_mode = False
            else:
                string_mode = True
        else:
            if string_mode:
                string += token
            else:
                if token != ' ':
                    # remove space tokens since they do not contribute to syntax
                    # identify the token
                    tokens.append(identify_token(token))
    return tokens


def _parse_array(tokens):
    i = 0
    result = []
    for token in tokens:
        i += 1
        if i % 2 == 0:
            if token != Comma:
                raise SyntaxError('Array syntax is `[item1, item2, ...]`')
        else:
            result.append(token)
    return result


def analise_tokens(tokens):
    ending = False
    if tokens[-1] == EndOfStatement:
        del tokens[-1]
        ending = True

    statement = parse_exp(tokens, ORDERED_OPERATORS, Statement)
    if isinstance(statement, Statement):
        statement._ending = ending
    else:
        statement = Statement([statement], ending=ending)

    # if tokens[0] == IfToken:
    #     if len(tokens) < 4 or \
    #             not (isinstance(tokens[1], Statement) and tokens[1].parenthesis == '()') or \
    #             tokens[2] != ThenToken:
    #         raise IfThenSyntaxError('If construction syntactically incorrect.')
    #
    #     statement = IfThenStatement(tokens[1], tokens[3], parenthesis=parenthesis, ending=ending)
    #     if len(tokens) >= 5 and tokens[4] == ElseToken:
    #         if len(tokens) > 6:
    #             raise IfThenSyntaxError('If construction syntactically incorrect.')
    #
    #         statement = IfThenStatement(tokens[1], tokens[3], _else=tokens[5], parenthesis=parenthesis,
    #                                     ending=ending)
    #     elif len(tokens) > 4:
    #         raise IfThenSyntaxError('If construction syntactically incorrect.')

    return statement


def _parse_block(all_tokens, start=0, block_lvl=0, parenthesis_lvl=0, rparenthesis_lvl=0):

    statements = []
    tokens = []
    i = start

    while i < len(all_tokens):
        token = all_tokens[i]

        # print(i, '%d%d%d' % (block_lvl, parenthesis_lvl, rparenthesis_lvl), token)
        if token == RParenthesisOpen:
            expression, size = _parse_block(all_tokens, i + 1,
                                            block_lvl=block_lvl,
                                            parenthesis_lvl=parenthesis_lvl,
                                            rparenthesis_lvl=rparenthesis_lvl+1)
            tokens.append(expression)
            i += size + 1
        elif token == ParenthesisOpen:
            expression, size = _parse_block(all_tokens, i + 1,
                                            block_lvl=block_lvl,
                                            parenthesis_lvl=parenthesis_lvl + 1,
                                            rparenthesis_lvl=rparenthesis_lvl)
            tokens.append(expression)
            i += size + 1
        elif token == BracketOpen:
            expression, size = _parse_block(all_tokens, i + 1,
                                            block_lvl=block_lvl + 1,
                                            parenthesis_lvl=parenthesis_lvl,
                                            rparenthesis_lvl=rparenthesis_lvl)
            tokens.append(expression)
            i += size + 1

        elif token == RParenthesisClose:
            if rparenthesis_lvl == 0:
                raise UnbalancedParenthesisSyntaxError('Trying to close right parenthesis without them opened.')

            if tokens:
                statements.append(tokens)
            return Array(_parse_array(statements[0])), i - start
        elif token == ParenthesisClose:
            if parenthesis_lvl == 0:
                raise UnbalancedParenthesisSyntaxError('Trying to close parenthesis without opened parenthesis.')

            if tokens:
                statements.append(analise_tokens(tokens))

            return Statement(statements, parenthesis='()'), i - start
        elif token == BracketClose:
            if block_lvl == 0:
                raise UnbalancedParenthesisSyntaxError('Trying to close brackets without opened brackets.')

            if tokens:
                statements.append(analise_tokens(tokens))

            return Code(statements), i - start
        elif token == EndOfStatement:
            tokens.append(EndOfStatement)
            statements.append(analise_tokens(tokens))
            tokens = []
        else:
            tokens.append(token)
        i += 1

    if block_lvl != 0 or rparenthesis_lvl != 0 or parenthesis_lvl != 0:
        raise UnbalancedParenthesisSyntaxError('Brackets not closed')

    if tokens:
        statements.append(analise_tokens(tokens))

    return Statement(statements), i - start


def parse(script):
    tokens = parse_strings(tokenize(script))
    return _parse_block(tokens)[0]
