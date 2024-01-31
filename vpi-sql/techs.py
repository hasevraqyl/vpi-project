class Techs(object):
    class T(object):
        def __init__(self, name, category, cost, number):
            self.name = name
            self.category = category
            self.cost = cost
            self.number = number

    _techslist = {
        T("Теория гиперсферы", "phys", 100.0, 1),
        T("Варп-двигатель", "phys", 100.0, 2),
        T("Квантовый уловитель", "phys", 200.0, 3),
        T("Силовое поле", "phys", 200.0, 4),
        T("Высокочастотные лазеры", "phys", 300.0, 5),
        T("Ловушка гравиволн", "phys", 400.0, 5),
        T("Плазменная физика", "phys", 500.0, 6),
        T("Квантовый радар", "phys", 600.0, 7),
        T("Гравитационный накопитель", "phys", 600.0, 8),
        T("Наниты", "phys", 700.0, 9),
        T("Сверхчастотные лазеры", "phys", 700.0, 10),
        T("Дезинтегратор", "phys", 800.0, 11),
        T("Физика античастиц", "phys", 900.0, 12),
        T("Монопольные бомбы", "phys", 1000.0, 13),
        T("Квантовый стабилизатор", "phys", 1000.0, 14),
        T("Квантовая телепортация", "phys", 1100.0, 15),
        T("Законы робототехники", "cyb", 100.0, 1),
        T("Квантовая информатика", "cyb", 300.0, 2),
        T("Армия роботов", "cyb", 400.0, 3),
        T("Цифровой гулаг", "cyb", 500.0, 4),
        T("Перенос сознания", "cyb", 1000.0, 5),
        T("Сингулярность", "cyb", 1100.0, 6),
    }

    def fetch_tech(cls, name):
        for t in cls._techslist:
            if t.name == name:
                return t.category, t.cost, t.number


class Buildings(object):
    """we will possibly be deprecating the limit"""

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
        B("Зоны", 2.0, 0.0, 0.0, 2.0, 1000),
    }

    """i need to rewrite this"""

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
