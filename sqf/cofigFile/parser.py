from sqf.base_tokenizer import tokenize

from sqf.types import Statement, Number, String, Boolean, Variable
from sqf.keywords import Keyword
from sqf.parser_types import Comment, Space, EndOfLine, Tab
from sqf.parser import parse_block, parse_strings_and_comments


def identify_token(token):
    if isinstance(token, (Comment, String)):
        return token
    elif token == ' ':
        return Space()
    elif token in ('\n', '\r\n'):
        return EndOfLine(token)
    elif token == '\t':
        return Tab()
    elif token in ('class', '(', ')', '[', ']', '{', '}', ';', '=', ','):
        return Keyword(token)
    elif token in ('true', 'false'):
        return Boolean(token == 'true')
    elif token == '#define':
        return Keyword('#define')
    else:
        try:
            return Number(int(token))
        except ValueError:
            try:
                return Number(float(token))
            except ValueError:
                return Variable(token)


def parse(script):
    tokens = [identify_token(x) for x in parse_strings_and_comments(tokenize(script))]
    return parse_block(tokens, lambda x: Statement(x), lambda x, _: [Statement(x)], stop_statement='single')[0]
