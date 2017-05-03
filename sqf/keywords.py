from sqf.types import Keyword
from sqf.expressions import BinaryExpression, UnaryExpression
from sqf.database import EXPRESSIONS

# keywords that are not commands, but part of the language
KEYWORDS = {'(', ')', '[', ']', '{', '}',',', '=', ';'}
KEYWORDS = KEYWORDS.union({'#define','#include', '\\'})

NULARY_OPERATORS = set()
UNARY_OPERATORS = set()
BINARY_OPERATORS = set()

for expression in EXPRESSIONS:
    if isinstance(expression, BinaryExpression):
        op = expression.types_or_values[1]
        BINARY_OPERATORS.add(op.value.lower())
    elif isinstance(expression, UnaryExpression):
        op = expression.types_or_values[0]
        UNARY_OPERATORS.add(op.value.lower())
    else:
        op = expression.types_or_values[0]
        NULARY_OPERATORS.add(op)

    KEYWORDS.add(op.value.lower())


OP_ARITHMETIC = [Keyword(s) for s in ('+', '-', '*', '/', '%', 'mod', '^', 'max', 'floor')]

OP_LOGICAL = [Keyword(s) for s in ('&&', 'and', '||', 'or')]

OP_COMPARISON = [Keyword(s) for s in ('==', 'isequalto', '!=', '<', '>', '<=', '>=', '>>')]

NAMESPACES = {'missionnamespace', 'profilenamespace', 'uinamespace', 'parsingnamespace'}

# namespaces are parsed as such
KEYWORDS = KEYWORDS - NAMESPACES

# operators by precedence. This is is used to build the lexical tree
ORDERED_OPERATORS = {
    -1: {'='},
    0: {'private'},
    1: {'||', 'or'},
    2: {'&&', 'and'},
    3: set(x.value for x in OP_COMPARISON),
    4.1: {'do'},
    4.2: {'catch', ':', 'then', 'exitwith', 'throw'},
    4.27: {'step', 'else'},
    4.28: {'to'},
    4.29: {'from'},
    4.3: {'if', 'try', 'case', 'while', 'switch', 'for'},
    6: {'+', 'str', 'hintC', 'hint', 'lbsetcursel', 'floor', 'ceil', 'round', 'random', 'max', 'min', '-'},
    6.1: {'count'},
    7: {'*', '/', '%', 'mod', 'atan2'},
    8: {'^'},
}

# all assigned
OTHERS = set()
for x in ORDERED_OPERATORS:
    OTHERS = OTHERS.union(ORDERED_OPERATORS[x])

# assign precedence to the remaining operators
NULARY_OPERATORS = NULARY_OPERATORS - OTHERS
UNARY_OPERATORS = UNARY_OPERATORS - OTHERS
# some ops are both binary and unary: make then unary for precedence
BINARY_OPERATORS = BINARY_OPERATORS - OTHERS - UNARY_OPERATORS

ORDERED_OPERATORS[5] = BINARY_OPERATORS
ORDERED_OPERATORS[9] = UNARY_OPERATORS
ORDERED_OPERATORS[10] = NULARY_OPERATORS
