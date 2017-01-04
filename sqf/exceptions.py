class NotATypeError(Exception):
    pass


class SQFSyntaxError(Exception):
    pass


class InterpreterError(Exception):
    pass


class IfThenSQFSyntaxError(SQFSyntaxError):
    pass


class UnbalancedParenthesisSQFSyntaxError(SQFSyntaxError):
    pass


class VariableNotDefined(InterpreterError):
    pass


class WrongTypes(InterpreterError):
    pass


class ExecutionError(InterpreterError):
    pass
