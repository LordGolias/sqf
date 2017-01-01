from arma3.interpreter import Interpreter, interpret
from arma3.types import Code, Array, String


class Client:
    def __init__(self):
        self._interpreter = Interpreter()
        self._interpreter.client = self
        self._listening_variables = {}  # var_name: code

    def set_sim(self, sim):
        self._interpreter.simulation = sim

    def add_listening(self, var_name, code):
        assert(isinstance(var_name, str) and isinstance(code, Code))
        self._listening_variables[var_name] = code

    def execute(self, code):
        interpret(code, self._interpreter)

    def set_variable(self, var_name, value, broadcast=True):
        self._interpreter.set_global_variable(var_name, value)

        if broadcast:
            if var_name in self._listening_variables:
                self._interpreter.execute_code(self._listening_variables[var_name],
                                               params=Array([String(var_name), value]))


class Simulation:

    def __init__(self):
        self.server = Client()
        self.server.set_sim(self)
        self._clients = []

        self._broadcasted = {}

    @property
    def clients(self):
        return self._clients

    def add_client(self, client):
        self._clients.append(client)
        client.set_sim(self)

        for var_name in self._broadcasted:
            client.set_variable(var_name, self._broadcasted[var_name], broadcast=False)

        return len(self._clients) - 1

    def broadcast(self, var_name, value, client_id=None):
        if client_id is None:
            self._broadcasted[var_name] = value
            for client in self._clients + [self.server]:
                client.set_variable(var_name, value)
        elif client_id == -1:
            self.server.set_variable(var_name, value)
        else:
            self._clients[client_id].set_variable(var_name, value)
