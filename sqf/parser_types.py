from sqf.base_type import ParserType


class Comment(ParserType):

    def __init__(self, string):
        super().__init__()
        if string.startswith('//'):
            self._line = True
        else:
            assert(string.startswith('/*'))
            self._line = False
        self._string = string

    def __str__(self):
        if self._line:
            return '%s' % self._string
        else:
            return '%s' % self._string

    def __repr__(self):
        return ('C(%s)' % self).replace('\n', ' ')


class Space(ParserType):
    def __str__(self):
        return ' '

    def __repr__(self):
        return '\' \''


class Tab(ParserType):
    def __str__(self):
        return '\t'

    def __repr__(self):
        return '\\t'


class EndOfLine(ParserType):
    def __init__(self, value):
        super().__init__()
        assert(value in ['\n', '\r\n'])
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return '<EOL>'


class BrokenEndOfLine(ParserType):
    def __str__(self):
        return '\\\n'

    def __repr__(self):
        return '<\EOL>'
