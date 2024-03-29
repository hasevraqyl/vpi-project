class Base(object):
    @classmethod
    def fetch(cls, name):
        return cls._list.get(name)


class Techs(Base):
    class T(object):
        def __init__(self, name, category, cost, number):
            self.name = name
            self.category = category
            self.cost = cost
            self.number = number

    _list = {
        "Теория гиперсферы": T("Теория гиперсферы", "phys", 100.0, 1),
        "Варп-двигатель": T("Варп-двигатель", "phys", 100.0, 2),
        "Квантовый уловитель": T("Квантовый уловитель", "phys", 200.0, 3),
        "Силовое поле": T("Силовое поле", "phys", 200.0, 4),
        "Высокочастотные лазеры": T("Высокочастотные лазеры", "phys", 300.0, 5),
        "Ловушка гравиволн": T("Ловушка гравиволн", "phys", 400.0, 5),
        "Плазменная физика": T("Плазменная физика", "phys", 500.0, 6),
        "Квантовый радар": T("Квантовый радар", "phys", 600.0, 7),
        "Гравитационный накопитель": T("Гравитационный накопитель", "phys", 600.0, 8),
        "Наниты": T("Наниты", "phys", 700.0, 9),
        "Сверхчастотные лазеры": T("Сверхчастотные лазеры", "phys", 700.0, 10),
        "Дезинтегратор": T("Дезинтегратор", "phys", 800.0, 11),
        "Физика античастиц": T("Физика античастиц", "phys", 900.0, 12),
        "Монопольные бомбы": T("Монопольные бомбы", "phys", 1000.0, 13),
        "Квантовый стабилизатор": T("Квантовый стабилизатор", "phys", 1000.0, 14),
        "Квантовая телепортация": T("Квантовая телепортация", "phys", 1100.0, 15),
        "Законы робототехники": T("Законы робототехники", "cyb", 100.0, 1),
        "Квантовая информатика": T("Квантовая информатика", "cyb", 300.0, 2),
        "Армия роботов": T("Армия роботов", "cyb", 400.0, 3),
        "Цифровой гулаг": T("Цифровой гулаг", "cyb", 500.0, 4),
        "Перенос сознания": T("Перенос сознания", "cyb", 1000.0, 5),
        "Сингулярность": T("Сингулярность", "cyb", 1100.0, 6),
    }


class Buildings(Base):
    """we will possibly be deprecating the limit"""

    class B(object):
        def __init__(self, name, cost, res, lim, buildtime, maxi, p, e, h, b):
            self.name = name
            self.cost = cost
            self.res = res
            self.lim = lim
            self.buildtime = buildtime
            self.maxi = maxi
            self.p = p
            self.e = e
            self.h = h
            self.b = b

    _list = {
        "Основные промзоны": B(
            "Основные промзоны", 2.0, 0.0, 0.0, 3, 1000, False, False, False, False
        ),
        "ВПК": B("ВПК", 3.0, 0.0, 0.0, 5, 1000, False, False, False, False),
        "Гражданский сектор": B(
            "Гражданский сектор", 2.0, 0.0, 0.0, 2, 1000, False, False, False, False
        ),
        "Технопарк": B("Технопарк", 5.0, 0.0, 0.0, 10, 1000, False, True, False, False),
        "Академия": B("Академия", 3.0, 0.0, 0.0, 3, 1000, False, True, False, False),
        "Кварталы I": B(
            "Кварталы I", 2.0, 0.0, 0.0, 1, 1000, False, False, True, False
        ),
        "Кварталы II": B(
            "Кварталы II", 2.0, 0.0, 0.0, 2, 1000, False, False, True, False
        ),
        "Кварталы III": B(
            "Кварталы III", 2.0, 0.0, 0.0, 4, 1000, False, False, True, False
        ),
        "Трущобы": B("Трущобы", 0.0, 0.0, 0.0, 1, 1000, False, False, True, False),
        "Зоны": B("Зоны", 2.0, 0.0, 0.0, 2, 1000, False, False, False, False),
        "Муниципалка": B(
            "Муниципалка", 3.0, 0.0, 0.0, 1, 1000, False, True, False, False
        ),
        "Верфь": B("Верфь", 5.0, 0.0, 0.0, 7, 10, True, False, False, False),
        "Аварийные кварталы": B(
            "Аварийные кварталы", 0.0, 0.0, 0.0, 0, 0, False, False, True, True
        ),
        "Шахта": B("Шахта", 1.0, 0.0, 0.0, 1, 1000, False, False, False, False),
        "Шахта Г": B("Шахта Г", 2.0, 0.0, 0.0, 2, 1000, False, False, False, False),
        "Шахта С": B("Шахта С", 2.0, 0.0, 0.0, 2, 1000, False, False, False, False),
        "Деловой центр": B(
            "Деловой центр", 3.0, 0.0, 0.0, 1, 1000, False, True, False, False
        ),
    }

    """
    @classmethod
    def stationcheck(cls, name):
        for type in cls._stationslist:
            if type.name == name:
                return True, type.buildtime
        return False, None

    @classmethod
    def stationcostfetch(cls, name):
        for type in cls._stationslist:
            if type.name == name:
                return type.cost
    """


"""
    @classmethod
    def buildingfetch(cls, name):
        for type in cls._buildingslist:
            if type.name == name:
                return type.maxi

    @classmethod
    def costfetch(cls, name):
        for type in cls._buildingslist:
            if type.name == name:
                return type.cost
                """


class Modules(Base):
    class M(object):
        def __init__(self, name, cost, lim, sil, prot, dmg, dmg_type, sn):
            self.name = name
            self.cost = cost
            self.op_lim = lim
            self.op_sil = sil
            self.prt = prot
            self.dmg = dmg
            self.dmg_type = dmg_type
            self.sn = sn

    _list = {"Ракеты": M("Ракеты", 20.0, 5.0, 0.0, 0.0, 0.0, "rocket", False)}
