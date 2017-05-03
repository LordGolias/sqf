from sqf.types import Code, String, Number, Array, Type, Variable


class InterpreterType(Type):
    # type that is used by the interpreter (e.g. While type)
    def __init__(self, token=None):
        assert (token is None or isinstance(token, Type))
        super().__init__()
        self.token = token


class PrivateType(InterpreterType):
    """
    A type to store the result of "private _x" as in "private _x = 2"
    """
    def __init__(self, variable):
        assert(isinstance(variable, Variable))
        super().__init__(variable)

    @property
    def variable(self):
        return self.token


class WhileType(InterpreterType):
    def __init__(self, condition):
        assert(condition is None or isinstance(condition, Code))
        if condition is None:
            condition = Code([])
        super().__init__(condition)

    @property
    def condition(self):
        return self.token


class ForType(InterpreterType):
    def __init__(self, variable=None, from_=None, to=None, step=None):
        if from_ is None:
            from_ = Number()
        if to is None:
            to = Number()
        if step is None:
            step = Number(1)
        assert (variable is None or isinstance(variable, String))
        assert (isinstance(from_, Type))
        assert (isinstance(to, Type))
        assert (isinstance(step, Type))
        super().__init__(variable)
        self.from_ = from_
        self.to = to
        self.step = step

    @property
    def variable(self):
        return self.token


class ForSpecType(InterpreterType):
    def __init__(self, array):
        assert (array is None or isinstance(array, Array))
        super().__init__(array)

    @property
    def array(self):
        return self.token


class SwitchType(InterpreterType):
    def __init__(self, result):
        super().__init__(result)

    @property
    def result(self):
        return self.token


class IfType(InterpreterType):
    def __init__(self, condition=None):
        super().__init__(condition)

    @property
    def condition(self):
        return self.token


class ElseType(InterpreterType):
    def __init__(self, then=None, else_=None):
        super().__init__(then)
        assert (then is None or isinstance(then, Code))
        assert (else_ is None or isinstance(else_, Code))
        self.else_ = else_

    @property
    def then(self):
        return self.token


class TryType(InterpreterType):
    def __init__(self, code=None):
        assert (code is None or isinstance(code, Code))
        super().__init__(code)

    @property
    def code(self):
        return self.token
