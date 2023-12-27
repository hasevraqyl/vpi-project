from Material import Material


class Resource(object):
    _material = Material()

    def get_Material(self):
        return self._material

    def set_Material(self, value):
        self._material = value
        return

    _quantity = 0

    def get_Quantity(self):
        return self._quantity

    def set_Quantity(self, value):
        self._quantity = value
        return
