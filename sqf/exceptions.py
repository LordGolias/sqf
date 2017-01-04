class SQFError(Exception):
    pass


class SQFParserError(SQFError):
    pass


class SQFParenthesisError(SQFParserError):
    pass


class SQFSyntaxError(SQFError):
    def __init__(self, position, message):
        self.position = position
        super().__init__('%s: %s' % (position, message))


class ExecutionError(SQFError):
    pass
