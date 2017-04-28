from sqf.types import Type, Array


class Object(Type):

    def __init__(self, pos):
        assert(isinstance(pos, Array))
        self._attrs = {'position': pos}


class Marker(Object):
    pass
