from core.types import Type, Array


class Object(Type):

    def __init__(self, pos):
        assert(isinstance(pos, Array))
        self._attrs = {'position': pos}

    def __getitem__(self, item):
        return self._attrs[item]

    def __setitem__(self, key, value):
        self._attrs[key] = value


class Marker(Object):
    pass
