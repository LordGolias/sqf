from sqf.base_type import BaseType
from sqf.types import Code, String, Number, Array, Type, Variable, Boolean


class InterpreterType(BaseType):
    # type that is used by the interpreter (e.g. While type)
    pass


class PrivateType(InterpreterType):
    """
    A type to store the result of "private _x" as in "private _x = 2"
    """
    def __init__(self, variable):
        assert(isinstance(variable, Variable))
        super().__init__()
        self.variable = variable


class WhileType(InterpreterType):
    def __init__(self, condition):
        assert(isinstance(condition, Code))
        super().__init__()
        self.condition = condition


class ForType(InterpreterType):
    def __init__(self, variable):
        assert (isinstance(variable, String))
        super().__init__()
        self.variable = variable


class ForSpecType(InterpreterType):
    def __init__(self, array):
        assert (isinstance(array, Array))
        super().__init__()
        self.array = array


class ForFromType(ForType):
    def __init__(self, variable, from_):
        assert (isinstance(from_, Type))
        super().__init__(variable)
        self.from_ = from_


class ForFromToStepType(ForFromType):
    def __init__(self, variable, from_, to, step=Number(1)):
        assert (isinstance(to, Type))
        assert (isinstance(step, Type))
        super().__init__(variable, from_)
        self.to = to
        self.step = step


class SwitchType(InterpreterType):
    def __init__(self, result):
        assert (isinstance(result, Type))
        super().__init__()
        self.result = result


class IfType(InterpreterType):
    def __init__(self, condition):
        assert (isinstance(condition, Type))
        super().__init__()
        self.condition = condition


class ElseType(InterpreterType):
    def __init__(self, then, else_):
        super().__init__()
        self.then = then
        self.else_ = else_
