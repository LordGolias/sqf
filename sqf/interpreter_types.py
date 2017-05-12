from sqf.types import Code, String, Number, Array, Type, Variable, Boolean, Nothing, Namespace


class InterpreterType(Type):
    # type that is used by the interpreter (e.g. While type)
    def __init__(self, token):
        assert (isinstance(token, Type))
        super().__init__()
        self.token = token

    @property
    def is_undefined(self):
        return self.token.is_undefined


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
        assert(isinstance(condition, Code))
        super().__init__(condition)

    @property
    def condition(self):
        return self.token


class ForType(InterpreterType):
    def __init__(self, variable=None, from_=None, to=None, step=None):
        if step is None:
            step = Number(1)
        if variable is None:
            variable = String()
        assert (variable is None or isinstance(variable, String))
        assert (from_ is None or isinstance(from_, Type))
        assert (to is None or isinstance(to, Type))
        assert (isinstance(step, Type))
        super().__init__(variable)
        self.from_ = from_
        self.to = to
        self.step = step

    @property
    def variable(self):
        return self.token

    @property
    def is_undefined(self):
        return self.variable.is_undefined or \
               self.from_ is not None and self.from_.is_undefined or \
               self.to is not None and self.to.is_undefined

    def copy(self, other):
        self.token = other.variable
        self.from_ = other.from_
        self.to = other.to
        self.step = other.step


class ForSpecType(InterpreterType):
    def __init__(self, array):
        assert (isinstance(array, Array))
        super().__init__(array)

    @property
    def array(self):
        return self.token


class SwitchType(InterpreterType):
    def __init__(self, keyword, result):
        super().__init__(result)
        self.keyword = keyword

    @property
    def result(self):
        return self.token


class IfType(InterpreterType):
    def __init__(self, condition=None):
        if condition is None:
            condition = Boolean()
        super().__init__(condition)

    @property
    def condition(self):
        return self.token


class ElseType(InterpreterType):
    def __init__(self, then, else_):
        super().__init__(then)
        assert (isinstance(then, Code))
        assert (isinstance(else_, Code))
        self.else_ = else_

    @property
    def then(self):
        return self.token

    @property
    def is_undefined(self):
        return self.else_.is_undefined or self.then.is_undefined


class TryType(InterpreterType):
    def __init__(self, code):
        assert (isinstance(code, Code))
        super().__init__(code)


class WithType(InterpreterType):
    def __init__(self, namespace):
        assert (isinstance(namespace, Namespace))
        super().__init__(namespace)

    @property
    def namespace(self):
        return self.token
