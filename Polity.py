from ITurnBased import ITurnBased
from IResourceHolder import IResourceHolder
from IdentityBase import IdentityBase


class Polity(IdentityBase, IResourceHolder, ITurnBased):
    _systems = []

    def get_Systems(self):
        return self._systems

    def set_Systems(self, value):
        self._systems = value
        return

    _resources = []

    def get_Resources(self):
        return self._resources

    def set_Resources(self, value):
        self._resources = value
        return

    def TurnPassed(self):
        for system in self._systems:
            print("passing system turn")
            if system.get_ReigningPolity() != self:
                system.set_ReigningPolity(self)
            system.TurnPassed()
        return
