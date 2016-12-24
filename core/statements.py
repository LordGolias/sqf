from core.types import EndOfStatement, IfToken, ThenToken, ElseToken


class Statement:
    def __init__(self, tokens, parenthesis=None):
        self._tokens = tokens
        self._parenthesis = parenthesis

    @property
    def parenthesis(self):
        return self._parenthesis

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, other):
        return self._tokens[other]

    def __str__(self):
        as_str = ''
        for i, s in enumerate(self._tokens):
            if i == 0 or s == EndOfStatement:
                as_str += '%s' % s
            else:
                as_str += ' %s' % s

        if self._parenthesis:
            as_str = '%s%s%s' % (self._parenthesis[0], as_str, self._parenthesis[1])
        return as_str

    def __repr__(self):
        return 'S<%s>' % self

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class BinaryStatement(Statement):
    def __init__(self, lhs, op, rhs):
        super().__init__([lhs, op, rhs])


class AssignmentStatement(BinaryStatement):
    pass


class LogicalStatement(BinaryStatement):
    pass


class IfThenStatement(Statement):
    def __init__(self, condition, outcome, _else=None):
        all = [IfToken, condition, ThenToken, outcome]
        if _else:
            all += [ElseToken, _else]
        super().__init__(all)
