class SQFError(Exception):
    pass


class SQFParserError(SQFError):
    """
    Raised by the parser and analyser
    """
    def __init__(self, position, message):
        assert(isinstance(position, tuple))
        self.position = position
        self.message = "Syntax error: %s" % message


class SQFParenthesisError(SQFParserError):
    pass


class SQFSyntaxError(SQFError):
    """
    Raised by the interpreter
    """
    def __init__(self, position, message):
        self.position = position
        super().__init__('%s: %s' % (position, message))


class ExecutionError(SQFError):
    pass
