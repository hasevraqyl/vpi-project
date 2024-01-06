from trash.ITurnBased import ITurnBased
from trash.IdentityBase import IdentityBase
from trash.Resource import Resource


class Province(IdentityBase, ITurnBased):
    def __init__(self, system, rp):
        self._reigningsystem = system
        self._rp = rp

    _bp = 0

    _tr = 0

    def get_BP(self):
        return self._bp

    def set_BP(self, value):
        self._bp = value
        return

    """when we have a normal init system
    we will have to clear stuff up"""

    def get_ReigningSystem(self):
        return self._reigningsystem

    _resourcesFromProvince = []

    def get_ResourcesFromProvince(self):
        return self._resourcesFromProvince

    def set_ResourcesFromProvince(self, value):
        self._resourcesFromProvince = value
        return

    def TurnPassed(self):
        print("passing province turn 2")
        for resource in self._resourcesFromProvince:
            total = resource.get_Quantity() + resource.get_TurnProduction()
            resource.set_Quantity(total)
        """this is the part that will get changed in the future"""
        reigningpolity = self._reigningsystem.get_ReigningPolity()
        if reigningpolity is None:
            return
        newRF = False
        polityFullResources = reigningpolity.get_Resources()
        politylen = 0
        if len(polityFullResources) != 0:
            i = 0
            for res in polityFullResources:
                if res.get_Material() == resource.get_Material():
                    newRF = True
                    politylen = i
                    print(politylen)
                    break
                i += 1
        if len(reigningpolity.get_Resources()) == 0 or not newRF:
            print("no nothin")
            polityResource = Resource()
            polityResource.set_Quantity(0)
            polityResource.set_Material(resource.get_Material())
            r = reigningpolity.get_Resources()
            politylen = len(r)
            r.append(polityResource)
            reigningpolity.set_Resources(r)
        polityResources = reigningpolity.get_Resources()
        polityResource = polityResources[politylen]
        polityResource.set_Quantity(
            polityResource.get_Quantity() + resource.get_TurnProduction()
        )
        reigningpolity.set_Money(reigningpolity.get_Money() + self._bp)
        self._tr = self._tr + (self._rp - self._bp)
        return
