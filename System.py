from ITurnBased import ITurnBased
from IdentityBase import IdentityBase


class System(IdentityBase, ITurnBased):
    """something something we will have to
    change this line below when we have normal init"""

    def __init__(self, polity=None):
        self._reigningpolity = polity

    def get_ReigningPolity(self):
        return self._reigningpolity

    def set_ReigningPolity(self, value):
        self._reigningpolity = value
        return

    _provinces = []

    def get_Provinces(self):
        return self._provinces

    def set_Provinces(self, value):
        self._provinces = value
        return

    def TurnPassed(self):
        for province in self._provinces:
            print("passing province turn")
            province.TurnPassed()
        return
