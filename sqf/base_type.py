

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
    column = len(lines[-1])
    return line, column


class BaseType:
    """
    This class is used to count the string-coordinate (line, column) of any element in a statement.
    This is used for identifying, in a script, the line and column of an error.
    It also defines the __eq__
    """
    def __init__(self):
        self._parent = None
        self._parent_index = None

    def set_parent(self, parent, index):
        self._parent = parent
        self._parent_index = index

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return equal_dicts(self.__dict__, other.__dict__, ('_parent', '_parent_index'))
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def position(self):
        if self._parent is None:
            return 1, 1
        return get_coord(self._parent.string_up_to(self._parent_index))


class ParserType(BaseType):
    # type ignored by the interpreter
    pass


class BaseTypeContainer(BaseType):

    def __init__(self, tokens):
        super().__init__()
        for i, s in enumerate(tokens):
            assert(isinstance(s, BaseType))
            s.set_parent(self, i)
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

    def _as_str(self, func=str, up_to=None):
        raise NotImplementedError

    @property
    def tokens(self):
        return self._tokens

    @property
    def base_tokens(self):
        return self._base_tokens

    def string_up_to(self, index):
        string = ''
        if self._parent is not None:
            string += self._parent.string_up_to(self._parent_index)
        return string + self._as_str(up_to=index)

    def __str__(self):
        return self._as_str()
