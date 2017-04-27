class SQFError(Exception):
    pass


class SQFParserError(SQFError):
    def __init__(self, position, message):
        assert(isinstance(position, tuple))
        self.position = position
        self.message = message


class SQFParenthesisError(SQFParserError):
    pass


class SQFSyntaxError(SQFError):
    def __init__(self, position, message):
        self.position = position
        super().__init__('%s: %s' % (position, message))


class ExecutionError(SQFError):
    pass
