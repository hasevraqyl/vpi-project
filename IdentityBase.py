from IHasIdentity import IHASIdentity


class IdentityBase(IHASIdentity):
    def __init__(self):
        self._id = 0
        self._name = ""
        self._description = ""

    _id = 0

    def get_ID(self):
        return self._id

    def set_ID(self, value):
        self._id = value
        return

    _name = ""

    def get_Name(self):
        return self._name

    def set_Name(self, value):
        self._name = value
        return

    _description = ""

    def get_Description(self):
        return self._description

    def set_Description(self, value):
        self._description = value
        return
