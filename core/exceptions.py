class NotATypeError(Exception):
    pass


class SyntaxError(Exception):
    pass


class InterpreterError(Exception):
    pass


class IfThenSyntaxError(SyntaxError):
    pass


class UnbalancedParenthesisSyntaxError(SyntaxError):
    pass


class VariableNotDefined(InterpreterError):
    pass


class WrongTypes(InterpreterError):
    pass


class ExecutionError(InterpreterError):
    pass