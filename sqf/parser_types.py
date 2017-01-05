from sqf.base_type import ParserType


class Comment(ParserType):

    def __init__(self, string):
        if string.startswith('//'):
            self._line = True
            string = string[2:]
        else:
            assert(string.startswith('/*'))
            self._line = False
            string = string[2:-2]
        self._string = string

    def __str__(self):
        if self._line:
            return '//%s' % self._string
        else:
            return '/*%s*/' % self._string

    def __repr__(self):
        return ('C(%s)' % self).replace('\n', ' ')


class Space(ParserType):
    def __str__(self):
        return ' '

    def __repr__(self):
        return '\' \''


class EndOfLine(ParserType):
    def __str__(self):
        return '\n'

    def __repr__(self):
        return '<EOL>'
