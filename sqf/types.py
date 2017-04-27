from sqf.exceptions import SQFError
from sqf.parser_types import ParserType
from sqf.keywords import Keyword
from sqf.base_type import BaseType, BaseTypeContainer


class Type(BaseType):
    pass


class ConstantValue(Type):
    def __init__(self, value=None):
        super().__init__()
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
        assert(value[0] == value[-1])
        assert (value[0] in ["'", '"'])
        self.container = value[0]
        super().__init__(value[1:-1])

    def __str__(self):
        return "%s%s%s" % (self.container, self.value, self.container)

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


class Array(Type, BaseTypeContainer):
    def __init__(self, tokens):
        Type.__init__(self)
        assert(all(not isinstance(t, ParserType) for t in tokens))
        if Keyword(',') in tokens:
            raise SQFError('Keyword "," cannot be an item of an Array')
        BaseTypeContainer.__init__(self, tokens)

    def __repr__(self):
        return self._as_str(repr)

    @staticmethod
    def _is_base_token(token):
        # ignore tokens that are not relevant for the interpreter
        return True

    def _as_str(self, func=str, up_to=None):
        if up_to is None:
            return '[%s]' % ','.join(func(item) for item in self._tokens)

        assert(up_to < len(self._tokens))
        inside = ''
        for i, item in enumerate(self._tokens):
            comma = ''
            if i != 0:
                comma = ','

            if i == up_to:
                if i != 0:
                    inside += comma
                break
            inside += comma + func(item)
        return '[' + inside

    @property
    def value(self):
        return self._tokens

    def extend(self, index):
        new_tokens = [Nothing] * (index - len(self._tokens) + 1)
        self._tokens += new_tokens
        self._update_base_tokens()
        return Nothing

    def append(self, token):
        self._tokens.append(token)
        self._update_base_tokens()

    def resize(self, count):
        if count > len(self._tokens):
            self.extend(count - 1)
        else:
            self._tokens = self._tokens[:count]
        self._update_base_tokens()
        return Nothing

    def reverse(self):
        self._tokens.reverse()
        self._update_base_tokens()
        return Nothing

    def add(self, other):
        self._tokens += other
        self._update_base_tokens()
        return Nothing

    def set(self, rhs_v):
        # https://community.bistudio.com/wiki/set
        assert(isinstance(rhs_v, Array))
        index = rhs_v.value[0].value
        value = rhs_v.value[1]

        if index >= len(self._tokens):
            self.extend(index)
        self._tokens[index] = value
        self._update_base_tokens()
        return Nothing


class Variable(Type):
    def __init__(self, name):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    def __str__(self):
        return self._name

    def __repr__(self):
        return 'V<%s>' % self


class _Statement(BaseTypeContainer):
    def __init__(self, tokens, parenthesis=None, ending=False):
        assert (isinstance(tokens, list))
        for i, s in enumerate(tokens):
            assert(isinstance(s, (Type, Keyword, Statement, ParserType)))

        super().__init__(tokens)

        self._parenthesis = parenthesis
        self._ending = ending

    @staticmethod
    def _is_base_token(token):
        # ignore tokens that are not relevant for the interpreter
        return not (isinstance(token, ParserType) or
                    isinstance(token, _Statement) and not token._parenthesis and not token.base_tokens)

    @property
    def ending(self):
        return self._ending

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, other):
        return self._tokens[other]

    def _as_str(self, func=str, up_to=-1):
        as_str = ''
        for i, s in enumerate(self._tokens):
            if i == up_to:
                break
            as_str += '%s' % func(s)

        if self._parenthesis is not None:
            as_str = '%s%s%s' % (self._parenthesis[0], as_str, self._parenthesis[1])
        if self.ending:
            as_str += ';'
        return as_str


class Statement(_Statement, BaseType):
    def __init__(self, tokens, parenthesis=False, ending=False):
        if parenthesis:
            parenthesis = '()'
        else:
            parenthesis = None
        super().__init__(tokens, parenthesis, ending)

    def __repr__(self):
        return 'S<%s>' % self._as_str(repr)


class Code(_Statement, Type):
    def __init__(self, tokens):
        super().__init__(tokens, parenthesis='{}')

    def __repr__(self):
        return '%s' % self._as_str(repr)
