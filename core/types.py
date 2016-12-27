from exceptions import *


class Type:

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class ConstantValue(Type):
    def __init__(self, value=None):
        self._value = value

    @property
    def value(self):
        return self._value


class Boolean(ConstantValue):
    def __init__(self, value):
        assert (value is True or value is False)
        super().__init__(value)

    def __str__(self):
        if self._value:
            return 'true'
        else:
            return 'false'

    def __repr__(self):
        return 'B<%s>' % self


class String(ConstantValue):

    def __init__(self, value):
        assert(isinstance(value, str))
        super().__init__(value)

    @property
    def string(self):
        return self.value

    def __str__(self):
        return '"%s"' % self.string

    def __repr__(self):
        return 's<%s>' % self


class Nothing(ConstantValue):
    def __str__(self):
        return 'Nothing'

    def __repr__(self):
        return '<%s>' % self
Nothing = Nothing()


class Number(ConstantValue):
    def __init__(self, value):
        assert(isinstance(value, (int, float)))
        super().__init__(value)

    def __str__(self):
        if isinstance(self._value, int):
            return '%d' % self._value
        # todo: use a better representation of float
        return '%2.2f' % self._value

    def __repr__(self):
        return 'N%s' % self


class Array(Type):
    def __init__(self, items):
        self._items = []
        # asserts below check that it is a list of the form `A,B,C`
        # where A B and C are instances of a Type.
        i = 0
        if Comma in items:
            raise SyntaxError('Array syntax is `[item1, item2, ...]`')
        self._items = items

    def __str__(self):
        return '[%s]' % ', '.join(str(item) for item in self._items)

    def __repr__(self):
        return 'A%s' % self

    @property
    def value(self):
        return self._items


class Variable(Type):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name

    def __repr__(self):
        return 'V<%s>' % self


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


class ReservedToken:
    def __init__(self, token):
        self._token = token

    def __str__(self):
        return self._token

    def __repr__(self):
        return 'R<%s>' % self._token


IfToken = ReservedToken('if')
ThenToken = ReservedToken('then')
ElseToken = ReservedToken('else')
ForEach = ReservedToken('foreach')
Private = ReservedToken('private')
ParenthesisOpen = ReservedToken('(')
ParenthesisClose = ReservedToken(')')
RParenthesisOpen = ReservedToken('[')
RParenthesisClose = ReservedToken(']')
BracketOpen = ReservedToken('{')
BracketClose = ReservedToken('}')
Comma = ReservedToken(',')
EndOfStatement = ReservedToken(';')
Nil = ReservedToken('nil')

RESERVED = [IfToken, ThenToken, ElseToken, ForEach, ParenthesisOpen, ParenthesisClose, RParenthesisOpen, RParenthesisClose,
            BracketOpen, BracketClose, Nil, Private, Comma, EndOfStatement]


RESERVED_MAPPING = dict()
for word in RESERVED:
    RESERVED_MAPPING[word._token] = word


OPERATORS = {
    '=': BinaryOperator,

    '+': BinaryOperator,
    '-': BinaryOperator,
    '*': BinaryOperator,
    '/': BinaryOperator,
    '%': BinaryOperator,
    'mod': BinaryOperator,
    '^': BinaryOperator,

    'setvariable': BinaryOperator,
    'getvariable': BinaryOperator,
    'set': BinaryOperator,
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
ORDERED_OPERATORS = [OPERATORS[s] for s in ('=', 'count', '>', 'units', 'SPAWN', 'spawn', 'alive', '&&', '!', 'getvariable')]

OP_ARITHMETIC = {OPERATORS[s] for s in ('+', '-', '*', '/', '%', 'mod', '^')}

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
}


def _subtract_lists(x, y):
    yset = set([y_i.value for y_i in y])
    return [x_i for x_i in x if x_i.value not in yset]


OP_ARRAY_OPERATIONS = {
    OPERATORS['+']: lambda x, y: x + y,
    OPERATORS['-']: lambda x, y: _subtract_lists(x, y),
}
