from sqf.base_tokenizer import tokenize

from sqf.types import Statement, Number, Boolean, Variable
from sqf.keywords import Keyword
from sqf.parser_types import Comment, Space, EndOfLine, Tab
from sqf.parser import parse_strings, parse_comments, parse_block


def identify_token(token):
    if isinstance(token, Comment):
        return token
    elif token == ' ':
        return Space()
    elif token == '\n':
        return EndOfLine()
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
    tokens = parse_strings(parse_comments(tokenize(script)), identify_token)
    return parse_block(tokens, lambda x: Statement(x), lambda x, _: [Statement(x)])[0]
