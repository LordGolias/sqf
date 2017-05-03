

def equal_dicts(d1, d2, ignore_keys):
    ignored = set(ignore_keys)
    for k1, v1 in d1.items():
        if k1 not in ignored and (k1 not in d2 or d2[k1] != v1):
            return False
    for k2, v2 in d2.items():
        if k2 not in ignored and k2 not in d1:
            return False
    return True


def get_coord(string):
    lines = string.split('\n')
    line = len(lines)
    column = len(lines[-1]) + 1
    return line, column
assert(get_coord('aa') == (1, 3))


def get_diff(string):
    lines = string.split('\n')
    line = len(lines) - 1
    column = len(lines[-1])
    return line, column
assert(get_diff('') == (0, 0))
assert(get_diff('aa') == (0, 2))
assert(get_diff('aa\n') == (1, 0))
assert(get_diff('aa\na') == (1, 1))


class BaseType:
    """
    This class is used to count the string-coordinate (line, column) of any element in a statement.
    This is used for identifying, in a script, the line and column of an error.
    It also defines the __eq__
    """
    def __init__(self):
        self._position = None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return equal_dicts(self.__dict__, other.__dict__, ('_parent', '_parent_index', '_position'))
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def position(self):
        if self._position is None:
            raise Exception(self, type(self))
        return self._position

    def set_position(self, position):
        assert(isinstance(position, tuple))
        assert (len(position) == 2)
        self._position = position

    @position.setter
    def position(self, self_position):
        self.set_position(self_position)


class ParserType(BaseType):
    # base type ignored by the interpreter
    pass


class BaseTypeContainer(BaseType):
    """
    This is the base class for containers (e.g. statements, code).

    Relevant of this class:
        * `base_tokens` to get tokens that have functionality.
        * `string_up_to`: the string representation of this class up to an index.
    """
    def __init__(self, tokens):
        super().__init__()
        for i, s in enumerate(tokens):
            assert(isinstance(s, BaseType))
        self._tokens = tokens

        self._update_base_tokens()

    def _update_base_tokens(self):
        self._base_tokens = []
        for token in self._tokens:
            if not self._is_base_token(token):
                continue
            self._base_tokens.append(token)

    @staticmethod
    def _is_base_token(token):
        raise NotImplementedError

    def _as_str(self, func=str):
        raise NotImplementedError

    def _column_delta(self, place='begin'):
        """
        Returns how much the column advances `place=` "begin" or "middle".
        """
        raise NotImplementedError

    def set_position(self, position):
        self._position = position
        position = (position[0], position[1] + self._column_delta())
        for token in self._tokens:
            token.set_position(position)

            token_delta = get_diff(str(token))

            if token_delta[0] == 0:
                initial_column = position[1]
            else:
                initial_column = 1

            position = (
                position[0] + token_delta[0],
                initial_column + token_delta[1] + self._column_delta('middle'))

    @BaseType.position.setter
    def position(self, position):
        super().set_position(position)

    @property
    def base_tokens(self):
        return self._base_tokens

    def __str__(self):
        return self._as_str()
