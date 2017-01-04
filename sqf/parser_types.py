
class ParserType:
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


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
