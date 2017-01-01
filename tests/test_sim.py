from unittest import TestCase

from arma3.types import Number as N, Nothing
from arma3.client import Simulation, Client


class Sim(TestCase):

    def test_broadcast(self):
        sim = Simulation()

        id = sim.add_client(Client())
        sim.clients[id].execute('"x" addPublicVariableEventHandler {y = _this select 1};')

        # broadcast at assignment and the PublicVariableEventHandler (PVEH)
        sim.server.execute('x = 123; publicVariable "x";')
        self.assertEqual(N(123), sim._clients[id]._interpreter['x'])
        self.assertEqual(N(123), sim._clients[id]._interpreter['y'])

        # broadcast to a JIP client updates the var but does not trigger the PVEH
        id = sim.add_client(Client())
        sim.clients[id].execute('"x" addPublicVariableEventHandler {y = _this select 1};')

        self.assertEqual(N(123), sim._clients[id]._interpreter['x'])
        self.assertEqual(Nothing, sim._clients[id]._interpreter['y'])

    def test_publicVariableOther(self):
        sim = Simulation()

        id0 = sim.add_client(Client())
        id1 = sim.add_client(Client())
        # to server
        sim.clients[id0].execute('x = 2; publicVariableServer "x";')
        self.assertEqual(N(2), sim.server._interpreter['x'])
        self.assertEqual(Nothing, sim.clients[id1]._interpreter['x'])

        # to client but not the server
        sim.clients[id0].execute('x = 3; 1 publicVariableClient "x";')
        self.assertEqual(N(2), sim.server._interpreter['x'])
        self.assertEqual(N(3), sim.clients[id1]._interpreter['x'])
