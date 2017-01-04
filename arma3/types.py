from arma3.exceptions import SQFSyntaxError
from arma3.parser_types import ParserType
from arma3.keywords import Keyword, Comma


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
        if Comma in items:
            raise SQFSyntaxError('Array syntax is `[item1, item2, ...]`')
        self._items = items

    def __str__(self):
        return '[%s]' % ','.join(str(item) for item in self._items)

    def __repr__(self):
        return '[%s]' % ','.join(repr(item) for item in self._items)

    @property
    def value(self):
        return self._items

    def extend(self, index):
        self._items += [Nothing] * (index - len(self._items) + 1)
        return Nothing

    def reverse(self):
        self._items.reverse()
        return Nothing

    def add(self, other):
        self._items += other
        return Nothing

    def set(self, rhs_v):
        # https://community.bistudio.com/wiki/set
        assert(isinstance(rhs_v, Array))
        index = rhs_v.value[0].value
        value = rhs_v.value[1]

        if index >= len(self._items):
            self.extend(index)
        self._items[index] = value
        return Nothing


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


class _Statement:
    def __init__(self, tokens, parenthesis=None, ending=False):
        assert (isinstance(tokens, list))
        for s in tokens:
            assert(isinstance(s, (Type, Keyword, Statement, ParserType)))
        self._tokens = tokens
        self._parenthesis = parenthesis
        self._ending = ending

        # ignore tokens that are not relevant for the interpreter
        self._base_tokens = []
        for token in self.tokens:
            if isinstance(token, ParserType):
                continue
            self._base_tokens.append(token)

    @property
    def tokens(self):
        return self._tokens

    @property
    def base_tokens(self):
        return self._base_tokens

    @property
    def ending(self):
        return self._ending

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, other):
        return self._tokens[other]

    def _as_str(self, func):
        as_str = ''
        for i, s in enumerate(self._tokens):
            as_str += '%s' % func(s)

        if self._parenthesis is not None:
            as_str = '%s%s%s' % (self._parenthesis[0], as_str, self._parenthesis[1])
        if self.ending:
            as_str += ';'
        return as_str

    def __str__(self):
        return self._as_str(str)

    def __repr__(self):
        return 'S<%s>' % self._as_str(repr)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Statement(_Statement):
    def __init__(self, tokens, parenthesis=False, ending=False):
        if parenthesis:
            parenthesis = '()'
        else:
            parenthesis = None
        super().__init__(tokens, parenthesis, ending)


class Code(_Statement, Type):
    def __init__(self, tokens):
        super().__init__(tokens, parenthesis='{}')

    def __repr__(self):
        return '%s' % self._as_str(repr)
