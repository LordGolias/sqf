import math


class Operator:

    def __init__(self, op):
        self._op = op

    @property
    def op(self):
        return self._op

    def __str__(self):
        return self.op

    def __repr__(self):
        return 'O<%s>' % self


class UnaryOperator(Operator):
    pass


class BinaryOperator(Operator):
    pass


OPERATORS = {
    'private': UnaryOperator,
    '=': BinaryOperator,

    '+': BinaryOperator,
    '-': BinaryOperator,
    '*': BinaryOperator,
    '/': BinaryOperator,
    '%': BinaryOperator,
    'mod': BinaryOperator,
    '^': BinaryOperator,
    'max': BinaryOperator,

    'floor': UnaryOperator,

    'setvariable': BinaryOperator,
    'getvariable': BinaryOperator,

    'set': BinaryOperator,
    'in': BinaryOperator,
    'select': BinaryOperator,
    'find': BinaryOperator,
    'append': BinaryOperator,
    'pushBack': BinaryOperator,
    'pushBackUnique': BinaryOperator,
    'reverse': UnaryOperator,

    'call': BinaryOperator,

    'spawn': BinaryOperator,
    'SPAWN': BinaryOperator,

    '&&': BinaryOperator,
    'and': BinaryOperator,
    '||': BinaryOperator,
    'or': BinaryOperator,

    'isEqualTo': BinaryOperator,
    '==': BinaryOperator,
    '!=':  BinaryOperator,
    '>': BinaryOperator,
    '<': BinaryOperator,
    '>=': BinaryOperator,
    '<=': BinaryOperator,

    '!': UnaryOperator,
    'not': UnaryOperator,
    'isNull': UnaryOperator,
    'isNil': UnaryOperator,
    'units': UnaryOperator,
    'count': BinaryOperator,
    'alive': UnaryOperator,
    'getmarkerpos': UnaryOperator,
}


for s in OPERATORS:
    OPERATORS[s] = OPERATORS[s](s)

# operators by precedence
ORDERED_OPERATORS = [OPERATORS[s] for s in ('private', '=', 'count', '>', 'units', 'SPAWN', 'spawn', 'alive', '&&', '!', 'getvariable')]

OP_ARITHMETIC = {OPERATORS[s] for s in ('+', '-', '*', '/', '%', 'mod', '^', 'max', 'floor')}

OP_LOGICAL = {OPERATORS[s] for s in ('&&', 'and', '||', 'or')}

OP_COMPARISON = {OPERATORS[s] for s in ('==', '!=', '<', '>', '<=', '>=')}

OP_OPERATIONS = {
    OPERATORS['+']: lambda x, y: x + y,
    OPERATORS['-']: lambda x, y: x - y,
    OPERATORS['*']: lambda x, y: x * y,
    OPERATORS['/']: lambda x, y: x / y,
    OPERATORS['%']: lambda x, y: x % y,
    OPERATORS['mod']: lambda x, y: x % y,
    OPERATORS['^']: lambda x, y: x ** y,

    OPERATORS['==']: lambda x, y: x == y,
    OPERATORS['!=']: lambda x, y: x != y,
    OPERATORS['<']: lambda x, y: x < y,
    OPERATORS['>']: lambda x, y: x < y,
    OPERATORS['<=']: lambda x, y: x <= y,
    OPERATORS['>=']: lambda x, y: x >= y,

    OPERATORS['&&']: lambda x, y: x and y,
    OPERATORS['and']: lambda x, y: x and y,
    OPERATORS['||']: lambda x, y: x or y,
    OPERATORS['or']: lambda x, y: x or y,

    OPERATORS['max']: lambda x, y: max(x, y),
    OPERATORS['floor']: lambda x: math.floor(x),
}


def _subtract_lists(x, y):
    yset = set([y_i.value for y_i in y])
    return [x_i for x_i in x if x_i.value not in yset]


OP_ARRAY_OPERATIONS = {
    OPERATORS['+']: lambda x, y: x + y,
    OPERATORS['-']: lambda x, y: _subtract_lists(x, y),
}
