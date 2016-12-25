from core.types import EndOfStatement, IfToken, ThenToken, ElseToken


class Statement:
    def __init__(self, tokens, parenthesis=None, ending=False):
        self._tokens = tokens
        self._parenthesis = parenthesis
        self._ending = ending

    @property
    def parenthesis(self):
        return self._parenthesis

    @property
    def ending(self):
        return self._ending

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, other):
        return self._tokens[other]

    def __str__(self):
        as_str = ''
        for i, s in enumerate(self._tokens):
            if i == 0:
                as_str += '%s' % s
            else:
                as_str += ' %s' % s

        if self.parenthesis:
            as_str = '%s%s%s' % (self.parenthesis[0], as_str, self.parenthesis[1])
        if self.ending:
            as_str += ';'
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


class IfThenStatement(Statement):
    def __init__(self, condition, outcome, _else=None, parenthesis=None, ending=False):
        self._condition = condition
        self._outcome = outcome
        self._else = _else

        all = [IfToken, condition, ThenToken, outcome]

        if _else:
            all += [ElseToken, _else]
        super().__init__(all, parenthesis=parenthesis, ending=ending)
