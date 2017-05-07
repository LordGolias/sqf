from sqf.exceptions import SQFError
from sqf.parser_types import ParserType
from sqf.base_type import BaseType, BaseTypeContainer


class Type(BaseType):
    """
    A type represents a type of variable. Every quantity that has a value is a type.
    """
    pass


class ConstantValue(Type):
    """
    A constant (literal) value. For example, a number, a string, code.
    """
    def __init__(self, value=None):
        super().__init__()
        self._value = value

    @property
    def value(self):
        return self._value


class Boolean(ConstantValue):
    def __init__(self, value=None):
        assert (value in (None,True,False))
        super().__init__(value)

    def __str__(self):
        if self._value is None:
            return 'undefined'
        if self._value:
            return 'true'
        else:
            return 'false'

    def __repr__(self):
        return 'B<%s>' % self


class String(ConstantValue):

    def __init__(self, value=None):
        self.container = None
        if value is not None:
            assert(isinstance(value, str))
            assert(value[0] == value[-1])
            assert (value[0] in ["'", '"'])
            self.container = value[0]
            super().__init__(value[1:-1])
        else:
            super().__init__(value)

    def __str__(self):
        if self.value is None:
            return "undefined"
        return "%s%s%s" % (self.container, self.value, self.container)

    def __repr__(self):
        return 's<%s>' % self


class Nothing(ConstantValue):
    """
    A type of unknown type
    """
    def __str__(self):
        return 'Nothing'

    def __repr__(self):
        return '<%s>' % self


class Number(ConstantValue):
    def __init__(self, value=None):
        assert(value is None or isinstance(value, (int, float)))
        super().__init__(value)

    def __str__(self):
        if self.value is None:
            return "undefined"
        if isinstance(self._value, int):
            return '%d' % self._value
        # todo: use a better representation of float
        return '%2.2f' % self._value

    def __repr__(self):
        return 'N%s' % self


class Array(Type, BaseTypeContainer):
    def __init__(self, tokens=None):
        Type.__init__(self)
        if tokens is not None:
            assert(all(not isinstance(t, ParserType) for t in tokens))
            if Keyword(',') in tokens:
                raise SQFError('Keyword "," cannot be an item of an Array')
            self._undefined = False
        else:
            self._undefined = True
            tokens = []
        BaseTypeContainer.__init__(self, tokens)

    def __repr__(self):
        return self._as_str(repr)

    @staticmethod
    def _is_base_token(token):
        # An array only holds relevant statements (or it is syntatically incorrect).
        return True

    def _column_delta(self, place='begin'):
        if place == 'begin':
            return 1  # [
        if place == 'middle':
            return 1  # ,

    def _as_str(self, func=str, up_to=None):
        if self._undefined:
            return '[undefined]'
        return '[%s]' % ','.join(func(item) for item in self._tokens)

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, other):
        assert(not self._undefined)
        return self._tokens[other]

    @property
    def value(self):
        if self._undefined:
            return None
        return self._tokens

    def extend(self, index):
        new_tokens = [Nothing()] * (index - len(self._tokens) + 1)
        self._tokens += new_tokens
        self._update_base_tokens()

    def append(self, token):
        self._tokens.append(token)
        self._update_base_tokens()

    def resize(self, count):
        if count > len(self._tokens):
            self.extend(count - 1)
        else:
            self._tokens = self._tokens[:count]
        self._update_base_tokens()

    def reverse(self):
        self._tokens.reverse()
        self._update_base_tokens()

    def add(self, other):
        self._tokens += other
        self._update_base_tokens()

    def set(self, rhs_v):
        # https://community.bistudio.com/wiki/set
        assert(isinstance(rhs_v, Array))
        index = rhs_v.value[0].value
        value = rhs_v.value[1]

        if index >= len(self._tokens):
            self.extend(index)
        self._tokens[index] = value
        self._update_base_tokens()


class Variable(Type):
    """
    A variable that holds values. It has a name (e.g. "_x").
    """
    def __init__(self, name):
        super().__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def is_global(self):
        return self.name[0] != '_'

    def __str__(self):
        return self._name

    def __repr__(self):
        return 'V<%s>' % self


class _Statement(BaseTypeContainer):
    def __init__(self, tokens, parenthesis=None, ending=''):
        assert (isinstance(tokens, list))
        for i, s in enumerate(tokens):
            assert(isinstance(s, (Type, Keyword, Statement, ParserType)))

        self._parenthesis = parenthesis
        self._ending = ending

        super().__init__(tokens)

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

    def _column_delta(self, place='begin'):
        if place == 'begin':
            if self.parenthesis is not None:
                return 1
        return 0

    def _as_str(self, func=str):
        if self._parenthesis:
            str_format = '{left}%s{right}'.format(left=self._parenthesis[0], right=self._parenthesis[1])
        else:
            str_format = '%s'
        str_format += self.ending

        return str_format % (''.join(func(item) for item in self._tokens))

    @property
    def parenthesis(self):
        return self._parenthesis


class Statement(_Statement, BaseType):
    """
    The main class for holding statements. It is a BaseType because it can be nested, and
    it is a _Statement because it can hold elements.
    """
    def __init__(self, tokens, parenthesis=False, ending=''):
        if parenthesis:
            parenthesis = '()'
        else:
            parenthesis = None
        super().__init__(tokens, parenthesis, ending)

    def __repr__(self):
        return 'S<%s>' % self._as_str(repr)


class Code(_Statement, Type):
    """
    The class that holds (non-interpreted) code.
    """
    def __init__(self, tokens):
        super().__init__(tokens, parenthesis='{}')

    def __repr__(self):
        return '%s' % self._as_str(repr)


class Keyword(BaseType):
    def __init__(self, token):
        assert isinstance(token, str)
        super().__init__()
        self._token = token
        self._unique_token = self._token.lower()

    @property
    def value(self):
        return self._token

    @property
    def unique_token(self):
        return self._unique_token

    def __str__(self):
        return self._token

    def __repr__(self):
        return 'K<%s>' % self._token

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._unique_token == other._unique_token
        else:
            return False

    def __hash__(self):
        return hash(str(self.__class__) + self.unique_token)


class Namespace(Type):
    def __init__(self, token):
        assert isinstance(token, str)
        super().__init__()
        self._token = token
        self._unique_token = token.lower()

    @property
    def value(self):
        return self._token

    def __repr__(self):
        return 'NS<%s>' % self._token

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._unique_token == other._unique_token
        else:
            return False


class Config(Type):

    def __init__(self, value=None):
        super().__init__()
        self._value = value

    @property
    def value(self):
        return self._value


class Object(Type):

    def __init__(self, value=None):
        super().__init__()
        self._value = value

    @property
    def value(self):
        return self._value


class File(Code):
    """
    Like code, but without parenthesis
    """
    def __init__(self, tokens):
        super().__init__(tokens)
        self._parenthesis = None

    def __repr__(self):
        return 'F<%s>' % self._as_str(repr)
