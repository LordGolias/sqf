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


class SQFWarning(SQFParserError):
    """
    Something that the interpreter understands but that is a bad practice or potentially
    semantically incorrect.
    """
    pass


class SQFSyntaxError(SQFParserError):
    """
    Raised by the interpreter
    """
    pass


class ExecutionError(SQFError):
    pass
