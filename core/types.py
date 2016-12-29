from core.exceptions import SyntaxError


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

    def __str__(self):
        return '"%s"' % self.value

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

    def set(self, index, value):
        self._items[index] = value

    def extend(self, index):
        self._items += [Nothing] * (index - len(self._items) + 1)

    def reverse(self):
        self._items.reverse()

    def append(self, other):
        self._items.append(other)

    def add(self, other):
        self._items += other


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
