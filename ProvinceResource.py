from Resource import Resource
from Province import Province
from Material import Material


class ProvinceResource(Resource):
    _turnProduction = 0

    def get_TurnProduction(self):
        return self._turnProduction

    def set_TurnProduction(self, value):
        self._turnProduction = value
        return

    _province = Province()

    def get_Province(self):
        return self._province

    def set_Province(self, value):
        if self._material is not None:
            if (
                self._province is not None
                and self._province in self._material.Provinces
            ):
                self._material.Provinces.remove(self._province)
        self._province = value
        self._material.Provinces.append(self._province)
        return

    _material = Material()

    def get_Material(self):
        return super().get_Material()

    def set_Material(self, value):
        if self._material is not None:
            if (
                self._province is not None
                and self._province in self._material.Provinces
            ):
                self._material.Provinces.remove(self._province)
        self._material = value
        self._material.Provinces.append(self._province)
        return

    def ProvinceResource():
        pass
