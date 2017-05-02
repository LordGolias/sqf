class SQFError(Exception):
    pass


class SQFParserException(SQFError):
    """
    Raised by the parser and analyser
    """
    def __init__(self, position, message):
        assert(isinstance(position, tuple))
        self.position = position
        self.message = message


class SQFParserError(SQFParserException):
    """
    Raised by the parser and analyser
    """
    def __init__(self, position, message):
        super().__init__(position, "error:%s" % message)


class SQFParenthesisError(SQFParserError):
    pass


class SQFWarning(SQFParserException):
    """
    Something that the interpreter understands but that is a bad practice or potentially
    semantically incorrect.
    """
    def __init__(self, position, message):
        super().__init__(position, "warning:%s" % message)


class SQFSyntaxError(SQFParserException):
    """
    Raised by the interpreter
    """
    pass


class ExecutionError(SQFError):
    pass
