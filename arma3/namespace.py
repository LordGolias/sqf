from arma3.types import Nothing


class Scope:

    def __init__(self, values=None):
        if values is None:
            values = {}
        self.values = values

    def __contains__(self, other):
        return other in self.values

    def __getitem__(self, name):
        if name in self.values:
            return self.values[name]
        else:
            return Nothing

    def __setitem__(self, item, value):
        self.values[item] = value


class Namespace:
    def __init__(self, all_vars=None):
        self._stack = [Scope(all_vars)]

    @property
    def current_scope(self):
        return self._stack[-1]

    @property
    def base_scope(self):
        return self._stack[0]

    def get_scope(self, name):
        if name.startswith('_'):
            for i in reversed(range(1, len(self._stack))):
                scope = self._stack[i]
                if name in scope:
                    return scope
            return self._stack[0]
        else:
            return self._stack[0]

    def add_scope(self, values=None):
        self._stack.append(Scope(values))

    def del_scope(self):
        del self._stack[-1]
