from exceptions import *


class Type:
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class String(Type):

    def __init__(self, tokens):
        assert(isinstance(tokens, str))
        self._tokens = tokens

    @property
    def string(self):
        return ''.join(self._tokens)

    def __str__(self):
        return '"%s"' % self.string

    def __repr__(self):
        return 's<%s>' % self


class Array(Type):
    def __init__(self, items):
        self._items = []
        # asserts below check that it is a list of the form `A,B,C`
        # where A B and C are instances of a Type.
        assert(len(items) == 1)
        i = 0
        for item in items[0]:
            i += 1
            if i % 2 == 0:
                if item != Comma:
                    raise SyntaxError('Array syntax is `[item1, item2, ...]`')
            else:
                self._items.append(item)

    def __str__(self):
        return '[%s]' % ', '.join(str(item) for item in self._items)

    def __repr__(self):
        return 'A%s' % self


class Nothing(Type):
    pass


class Variable(Type):
    def __init__(self, name):
        self._name = name

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
    '*': BinaryOperator,
    'setvariable': BinaryOperator,
    'getvariable': BinaryOperator,
    'set': BinaryOperator,
    'spawn': BinaryOperator,
    'SPAWN': BinaryOperator,
    '==': BinaryOperator,
    '!=':  BinaryOperator,
    '&&': BinaryOperator,
    'and': BinaryOperator,
    '||': BinaryOperator,
    'or': BinaryOperator,
    '!': UnaryOperator,
    '>': BinaryOperator,
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


LOGICAL_OPERATORS = {OPERATORS['=='], OPERATORS['!='], OPERATORS['||'], OPERATORS['&&']}
ASSIGMENT_OPERATORS = {OPERATORS['='], OPERATORS['setvariable'], OPERATORS['set']}
