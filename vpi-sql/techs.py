class Techs(object):
    class Tech(object):
        def __init__(self, name, number):
            self.name = name
            self.number = number


class Buildings(object):
    class B(object):
        def __init__(self, name, cost, res, lim, buildtime, maxi):
            self.name = name
            self.cost = cost
            self.res = res
            self.lim = lim
            self.buildtime = buildtime
            self.maxi = maxi

    _buildingslist = {
        B("Основные промзоны", 2.0, 0.0, 0.0, 3, 1000),
        B("ВПК", 3.0, 0.0, 0.0, 5, 1000),
        B("Гражданский сектор", 2.0, 0.0, 0.0, 2, 1000),
        B("Технопарк", 5.0, 0.0, 0.0, 10, 1000),
        B("Академия", 3.0, 0.0, 0.0, 3, 1000),
        B("Кварталы I", 2.0, 0.0, 0.0, 1, 1000),
        B("Кварталы II", 2.0, 0.0, 0.0, 2, 1000),
        B("Кварталы III", 2.0, 0.0, 0.0, 4, 1000),
        B("Трущобы", 0.0, 0.0, 0.0, 1, 1000),
    }

    def buildingcheck(cls, name):
        for type in cls._buildingslist:
            if type.name == name:
                return True, type.buildtime
        return False, None

    def buildingfetch(cls, name):
        for type in cls._buildingslist:
            if type.name == name:
                return type.maxi

    def costfetch(cls, name):
        for type in cls._buildingslist:
            if type.name == name:
                return type.cost
