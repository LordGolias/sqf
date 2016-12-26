class NotATypeError(Exception):
    pass


class SyntaxError(Exception):
    pass


class IfThenSyntaxError(SyntaxError):
    pass


class UnbalancedParenthesisSyntaxError(SyntaxError):
    pass
