from core.base_tokenizer import tokenize
from exceptions import NotATypeError, SyntaxError
from core.reserved_words import *
from core.types import *
from core.statements import *


test = """
_n = 0;
{
if (!isNil{_x getvariable "AirS"} && {{alive _x} count units _x > 0}) then {
_nul = [_x, (getmarkerpos "WestChopStart"),5] SPAWN FUNKTIO_MAD;
if (!isNull _x) then {_x setvariable ["AirS",nil];};
_n = 1;
};
sleep 0.1;
} foreach allgroups;

if (_n == 1) then {"Air support called to pull away" SPAWN HINTSAOK;} else {"You have no called air support operating currently" SPAWN HINTSAOK;};
"""


def identify_token(token):
    if token in OPERATORS:
        return OPERATORS[token]
    if token in RESERVED_MAPPING:
        return RESERVED_MAPPING[token]
    if token == ';':
        return EndOfStatement
    else:
        return Variable(token)


def parse_strings(all_tokens):
    tokens = []
    string_mode = False
    string = []
    for i, token in enumerate(all_tokens):
        if token == '"':
            if string_mode:
                tokens.append(String(string))
                string = []
                string_mode = False
            else:
                string_mode = True
        else:
            if string_mode:
                string.append(token)
            else:
                if token != ' ':
                    # remove space tokens since they do not contribute to syntax
                    # identify the token
                    tokens.append(identify_token(token))
    return tokens


def next_is_ending(all_tokens, i):
    return i + 1 < len(all_tokens) and all_tokens[i + 1] == EndOfStatement


def analize_tokens(statements):
    statement = Statement(statements)

    if isinstance(statements[1], BinaryOperator):
        if len(statements) < 3:
            raise SyntaxError

        if statements[1] in ASSIGMENT_OPERATORS:
            statement = AssignmentStatement(statements[0], statements[1], statements[2])
        elif statements[1] in LOGICAL_OPERATORS:
            statement = LogicalStatement(statements[0], statements[1], statements[2])
        else:
            statement = BinaryStatement(statements[0], statements[1], statements[2])

        if len(statements) > 3:
            statement = Statement([statement] + statements[3:])
    elif statements[0] == IfToken:
        if len(statements) < 4 or \
                not (isinstance(statements[1], Statement) and statements[1].parenthesis == '()') or \
                    statements[2] != ThenToken:
            raise SyntaxIfThenError('If construction syntactically incorrect.')

        statement = IfThenStatement(condition=statements[1], outcome=statements[3])
        if len(statements) >= 5 and statements[4] == ElseToken:
            statement = IfThenStatement(condition=statements[1], outcome=statements[3], _else=statements[5])
            print(repr(statement), repr(statement[0]))
            if len(statements) > 5:
                statement = Statement([statement] + statements[6:])
                print(repr(statement[0]), repr(statement[0][0]))
        elif len(statements) > 4:
            statement = Statement([statement] + statements[4:])

    return statement


def _parse_block(all_tokens, start=0, block_lvl=0, parenthesis_lvl=0, rparenthesis_lvl=0):

    statements = []
    statement = []
    i = start

    while i < len(all_tokens):
        token = all_tokens[i]

        #print(i, '%d%d%d' % (block_lvl, parenthesis_lvl, rparenthesis_lvl), token)
        if block_lvl and token == '}':
            raise Exception('Close bracket without open bracket.')

        if token == RParenthesisOpen:
            expression, size = _parse_block(all_tokens, i + 1,
                                            block_lvl=block_lvl,
                                            parenthesis_lvl=parenthesis_lvl,
                                            rparenthesis_lvl=rparenthesis_lvl+1)
            statement.append(expression)
            i += size + 1
        elif token == ParenthesisOpen:
            expression, size = _parse_block(all_tokens, i + 1,
                                            block_lvl=block_lvl,
                                            parenthesis_lvl=parenthesis_lvl + 1,
                                            rparenthesis_lvl=rparenthesis_lvl)
            statement.append(expression)
            i += size + 1
        elif token == BracketOpen:
            expression, size = _parse_block(all_tokens, i + 1,
                                            block_lvl=block_lvl + 1,
                                            parenthesis_lvl=parenthesis_lvl,
                                            rparenthesis_lvl=rparenthesis_lvl)
            statement.append(expression)
            i += size + 1

        elif token == RParenthesisClose:
            if rparenthesis_lvl == 0:
                raise Exception('Trying to close right parenthesis without them opened.')

            if statement:
                statements.append(statement)
            return Array(statements), i - start
        elif token == ParenthesisClose:
            if parenthesis_lvl == 0:
                raise Exception('Trying to close parenthesis without opened parenthesis.')

            if statement:
                statements.append(analize_tokens(statement))
            return Statement(statements, parenthesis='()'), i - start
        elif token == BracketClose:
            if parenthesis_lvl != 0:
                raise Exception('Trying to close brackets with opened brackets.')
            if block_lvl == 0:
                raise Exception('Trying to close brackets without opened brackets.')

            if statement:
                statements.append(analize_tokens(statement))
            return Statement(statements, parenthesis='{}'), i - start
        elif token == EndOfStatement:
            assert(isinstance(statement, list))
            statement.append(EndOfStatement)
            statements.append(analize_tokens(statement))
            statement = []
        else:
            statement.append(token)
        i += 1

    return Statement(statements), i - start


def parse(script):
    tokens = parse_strings(tokenize(script))
    return _parse_block(tokens)[0]


# if __name__ == '__main__':
#
#     test = '''
#     private ["_text","_f"];
#     _f = diag_fps;
#     _text = format ["Units %1 Groups %2 DeadUnits %3 Vehicles %4 FPS %5 CIVLIANS %6 EAST %7 WEST %8 OBJECTS %9 ENTITES %10",count Allunits, count allgroups, count alldeadmen, count vehicles,diag_fps, {side _x == CIVILIAN} count allunits, {side _x == EAST} count allunits, {side _x == WEST} count allunits,count allMissionObjects "All",count entities "All"];
#     hint _text;
# '''
#     print(len(parse(test)))
#     print(str(parse(test)))
