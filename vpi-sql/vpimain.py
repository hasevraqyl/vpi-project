import sqlite3
from enum_implement import DiscordStatusCode
from techs import Buildings
import numpy as np
import random

random.seed()

con = sqlite3.connect("vpi.db")
cur = con.cursor()


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def comma_stringer(bad_list):
    string = ""
    i = 0
    for elem in bad_list:
        i += 1
        if i == len(bad_list):
            string += "{}".format(elem[0])
            string += "."
        else:
            string += "{}".format(elem[0])
            string += ", "
    return string


def check_table():
    r = cur.execute("SELECT name from sqlite_master WHERE name = 'systems'")
    if r.fetchone() is None:
        print("таблицы нету")
        return False
    return True


def calculate_bp(bp_total, builds):
    for b in builds:
        if b[0] == "Основные промзоны" and b[1] == 0:
            bp_total = bp_total + 3.0
    return bp_total


def calculate_housing(builds):
    total_housing = 0
    housing = ["Кварталы I", "Кварталы II", "Кварталы III", "Трущобы"]
    for b in builds:
        if b[0] in housing and b[1] == 0:
            total_housing = total_housing + 1.0
    return total_housing


"""temporary function"""


def calculate_employment(builds):
    return 1.0


def calc_pop():
    li = list(cur.execute("SELECT polity_1, polity_2 from agreements"))
    agrl = []
    for e in li:
        for zone in agrl:
            if e[0] in zone and e[1] not in zone:
                zone.append(e[1])
            elif e[0] not in zone and e[1] not in zone:
                agrl.append([e[0], e[1]])
    lipol = list(cur.execute("SELECT polity_id from polities"))
    for e in lipol:
        f = False
        for zone in agrl:
            if e[0] in zone:
                f = True
                break
        if not f:
            agrl.append([[e[0]]])
    for zone in agrl:
        array = []
        pops = []
        for polity in zone:
            planets = list(
                cur.execute(
                    "SELECT planet from systems where polity_id = ?", tuple(polity)
                )
            )
            for planet in planets:
                res = list(
                    cur.execute(
                        "SELECT pop, RO, GP, VP, BP from resources where planet = ?",
                        (planet),
                    )
                )[0]
                housing = len(
                    list(
                        cur.execute(
                            """SELECT building from buildings WHERE building = ('Кварталы I'
                                                    OR building = 'Кварталы II'
                                                    OR building = 'Кварталы III'
                                                    OR building = 'Кварталы III'
                                                    OR building = 'Трущобы')
                                                    AND planet = ?""",
                            (planet),
                        )
                    )
                )
                promz = len(
                    list(
                        cur.execute(
                            """SELECT building from buildings WHERE building = 'Основные промзоны' AND planet = ?""",
                            (planet),
                        )
                    )
                )
                jobs = res[1] + res[2] + res[3] + res[4] + promz * 3
                total = housing * 5 + jobs
                pops.append(res[0])
                array.append(total)
        s = sum(array)
        for i in range(len(array)):
            array[i] = array[i] / s
        ea = np.array(array)
        ep = np.array(sum(pops))
        eq = np.multiply(ea, ep)
        newpop = []
        for i in range(len(pops)):
            newpop.append(pops[i] * 0.9 + eq[i] * 0.1)
        for i in range(len(planets)):
            res2 = list(
                cur.execute(
                    "SELECT RO, BP, GP, VP, RS, pop from resources where planet = ?",
                    planets[i],
                )
            )[0]
            cur.execute("DELETE from resources where planet = ?", (planets[i]))
            cur.executemany(
                "INSERT into resources VALUES(?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        planets[i][0],
                        res2[0],
                        res2[1],
                        res2[2],
                        res2[3],
                        res2[4],
                        newpop[i],
                    )
                ],
            )
    con.commit()


def calc_transfer():
    li = list(cur.execute("SELECT planetfrom, planetto FROM population_transfers"))
    for e in li:
        sys1 = list(
            cur.execute("SELECT polity_id from systems where planet = ?", (e[0],))
        )
        sys2 = list(
            cur.execute("SELECT polity_id from systems where planet = ?", (e[1],))
        )
        if sys1[0] != sys2[0]:
            cur.executemany(
                "DELETE FROM population_transfers where planetfrom = ? AND planetto = ?",
                [
                    (
                        e[0],
                        e[1],
                    )
                ],
            )
        else:
            pol = list(
                cur.execute(
                    "SELECT polity_name, polity_desc, creds from polities where polity_id = ?",
                    sys1[0],
                )
            )[0]
            cur.execute("DELETE from polities WHERE polity_id = ?", sys1[0])
            cur.executemany(
                "INSERT INTO polities VALUES(?, ?, ?, ?)",
                [
                    (
                        sys1[0][0],
                        pol[0],
                        pol[1],
                        (pol[2] - 10),
                    )
                ],
            )
        fromplanet = list(
            cur.execute(
                "SELECT pop, RO, BP, GP, VP, RS FROM resources WHERE planet = ?",
                (e[0],),
            )
        )[0]
        frompop = fromplanet[0]
        transfer = 0
        if frompop < 1.2:
            transfer = frompop
            frompop = 0
            cur.execute(
                "DELETE FROM population_transfers where planetfrom = ?", (e[0],)
            )
        else:
            frompop = frompop - 1
            transfer = 1
        toplanet = list(
            cur.execute(
                "SELECT pop, RO, BP, GP, VP, RS FROM resources WHERE planet = ?",
                (e[1],),
            )
        )[0]
        topop = toplanet[0]
        topop = topop + transfer
        cur.execute("DELETE FROM resources where planet = ?", (e[0],))
        cur.executemany(
            "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    e[0],
                    fromplanet[1],
                    fromplanet[2],
                    fromplanet[3],
                    fromplanet[4],
                    fromplanet[5],
                    frompop,
                )
            ],
        )
        cur.execute("DELETE FROM resources where planet = ?", (e[1],))
        cur.executemany(
            "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    e[1],
                    toplanet[1],
                    toplanet[2],
                    toplanet[3],
                    toplanet[4],
                    toplanet[5],
                    topop,
                )
            ],
        )
    con.commit()


class Game(object):
    """@classmethod
    def debug_pop(cls):
        calc_pop()"""

    @classmethod
    def calculate_ql(cls, pln):
        if not check_table():
            return None, DiscordStatusCode.no_table
        buildings = list(
            cur.execute(
                "SELECT building, turns_remains FROM buildings where planet = ?", (pln,)
            )
        )
        if len(buildings) == 0:
            return None, DiscordStatusCode.no_elem
        ql = 0.0
        qu_n = 0.0
        for build in buildings:
            if build[0] == (
                "Кварталы I" or "Кварталы II" or "Кварталы III" or "Трущобы"
            ):
                if build[1] == 0:
                    qu_n += 1.0
        res = list(
            cur.execute(
                "SELECT pop FROM resources WHERE planet = ?",
                (pln,),
            )
        )[
            0
        ][0]
        ql = 50 * qu_n / (res)
        return ql, DiscordStatusCode.all_clear

    @classmethod
    def rollback(cls):
        print("откачено!!!!!!")
        cur.execute("DROP TABLE IF EXISTS polities")
        cur.execute("DROP TABLE IF EXISTS systems")
        cur.execute("DROP TABLE IF EXISTS resources")
        cur.execute("DROP TABLE IF EXISTS buildings")
        cur.execute("DROP TABLE IF EXISTS stations")
        cur.execute("DROP TABLE IF EXISTS agreements")
        cur.execute("DROP TABLE IF EXISTS historical_planet")
        cur.execute("DROP TABLE IF EXISTS historical_polity")
        cur.execute("DROP TABLE IF EXISTS population_transfers")
        cur.execute("DROP TABLE IF EXISTS unclaimed_systems")
        cur.execute("DROP TABLE IF EXISTS unclaimed_planets")
        cur.execute(
            """CREATE TABLE polities (
    polity_id INTEGER   PRIMARY KEY
                        UNIQUE
                        NOT NULL,
    polity_name    TEXT UNIQUE
                        NOT NULL,
    polity_desc    TEXT,
    creds          REAL NOT NULL
                        DEFAULT (0.0) );"""
        )
        polities = [
            (1, "pogglia", "no sex", 0.0),
            (2, "ubia", "sex", 0.0),
        ]
        cur.executemany("INSERT INTO polities VALUES(?, ?, ?, ?)", polities)
        cur.execute(
            """CREATE TABLE resources (
    planet TEXT PRIMARY KEY
                UNIQUE
                NOT NULL,
    RO     REAL NOT NULL
                DEFAULT (0.0),
    BP     REAL NOT NULL
                DEFAULT (0.0),
    GP     REAL NOT NULL
                DEFAULT (0.0),
    VP     REAL NOT NULL
                DEFAULT (0.0),
    RS     REAL NOT NULL
                DEFAULT (0.0),
    pop    REAL NOT NULL
                DEFAULT (0.0));"""
        )
        resources = [
            ("moskvabad", 12.0, 7.0, 1.0, 1.0, 0.0, 10.0),
            ("rashidun", 12.0, 3.0, 1.0, 1.0, 0.0, 5.0),
            ("zumbia", 20.0, 4.0, 1.0, 1.0, 0.0, 10.0),
            ("ubia", 11.0, 6.0, 1.0, 1.0, 0.0, 4.0),
        ]
        cur.executemany("INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?)", resources)
        cur.execute(
            """CREATE TABLE systems (
    polity_id INTEGER NOT NULL,
    system    TEXT    NOT NULL,
    planet    TEXT    UNIQUE
                      NOT NULL
);"""
        )
        planets = [
            (1, "poggl-loire", "moskvabad"),
            (1, "poggl-loire", "rashidun"),
            (2, "ub-burgundy", "zumbia"),
            (2, "ub-burgundy", "ubia"),
        ]
        cur.executemany("INSERT INTO systems VALUES(?, ?, ?)", planets)
        cur.execute(
            """CREATE TABLE buildings (
    planet TEXT       NOT NULL,
    building TEXT     NOT NULL,
    turns_remains INT NOT NULL,
    id            INT NOT NULL
        )"""
        )
        cur.execute(
            """CREATE TABLE stations (
    system TEXT       NOT NULL,
    station TEXT     NOT NULL,
    turns_remains INT  NOT NULL
        )"""
        )
        cur.execute(
            """CREATE TABLE agreements (
    polity_1 TEXT    NOT NULL,
    polity_2 TEXT    NOT NULL
            )"""
        )
        cur.execute(
            """CREATE TABLE historical_planet (
    planet TEXT NOT NULL,
    RO     REAL NOT NULL
                DEFAULT (0.0),
    BP     REAL NOT NULL
                DEFAULT (0.0),
    GP     REAL NOT NULL
                DEFAULT (0.0),
    VP     REAL NOT NULL
                DEFAULT (0.0),
    RS     REAL NOT NULL
                DEFAULT (0.0),
    pop    REAL NOT NULL
                DEFAULT (0.0),
    turn   INT  NOT NULL
    );
        """
        )
        cur.execute(
            """CREATE TABLE population_transfers(
        planetfrom TEXT NOT NULL,
        planetto   TEXT NOT NULL
        )
"""
        )
        cur.execute(
            """CREATE TABLE historical_polity(
            polity_id INTEGER
                        NOT NULL,
    polity_name    TEXT
                        NOT NULL,
    polity_desc    TEXT,
    creds          REAL NOT NULL
                        DEFAULT (0.0),
    turn           INT  NOT NULL
        )"""
        )
        cur.execute(
            """CREATE TABLE unclaimed_systems(
                    system TEXT   NOT NULL,
                    planet TEXT   UNIQUE
                                  NOT NULL
        )"""
        )
        cur.execute(
            """CREATE TABLE unclaimed_planets(
            planet TEXT PRIMARY KEY
                        UNIQUE
                        NOT NULL,
            RO     REAL NOT NULL
                DEFAULT (0.0),
            BP     REAL NOT NULL
                DEFAULT (0.0),
            GP     REAL NOT NULL
                DEFAULT (0.0),
            VP     REAL NOT NULL
                DEFAULT (0.0)
        )"""
        )
        con.commit
        return DiscordStatusCode.all_clear

    @classmethod
    def turn(cls):
        if not check_table():
            return DiscordStatusCode.no_table
        for row in list(
            cur.execute(
                "SELECT polity_id, polity_name, polity_desc, creds FROM polities"
            )
        ):
            turnpol = list(
                cur.execute(
                    "SELECT MAX(turn) from historical_polity where polity_id = ?",
                    (row[0],),
                )
            )[0][0]
            if turnpol is None:
                turnpol = 1
            cur.executemany(
                "INSERT INTO historical_polity VALUES(?, ?, ?, ?, ?)",
                [
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        turnpol,
                    )
                ],
            )
            for row2 in list(
                cur.execute(
                    "SELECT system, planet FROM systems WHERE polity_id = ?", (row[0],)
                )
            ):
                for row3 in list(
                    cur.execute(
                        "SELECT RO, BP, RS, GP, VP, pop FROM resources WHERE planet = ?",
                        (row2[1],),
                    )
                ):
                    """do note resources are stored in NEGATIVE numbers
                    and converted to positive on the point of access
                    idk why i have to do this it breaks otherwise (actually i now know why nvm)
                    """
                    builds = list(
                        cur.execute(
                            "select building, turns_remains, id from buildings where planet = ?",
                            (row2[1],),
                        )
                    )
                    """coefpop will later be calculated through other means"""
                    coefpop = row3[5] / calculate_employment(builds)
                    if coefpop > 1:
                        coefpop = 1
                    coefhouse = calculate_housing(builds) / row3[5]
                    coeftotal = (coefpop * 0, 3 + coefhouse * 0, 7)
                    bp = calculate_bp(row3[1], builds)
                    rsnew = row3[2] + ((row3[0] - bp) * coeftotal)
                    popnew = row3[5] * 1.01
                    cur.execute("DELETE from resources WHERE planet = ?", (row2[1],))
                    cur.executemany(
                        "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?)",
                        [
                            (
                                row2[1],
                                row3[0],
                                row3[1],
                                row3[3],
                                row3[4],
                                rsnew,
                                popnew,
                            ),
                        ],
                    )
                    turn = list(
                        cur.execute(
                            "SELECT MAX(turn) FROM historical_planet where planet = ?",
                            (row2[1],),
                        )
                    )[0][0]
                    if turn is None:
                        turn = 1
                    cur.executemany(
                        "INSERT INTO historical_planet VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                        [
                            (
                                row2[1],
                                row3[0],
                                row3[1],
                                row3[3],
                                row3[4],
                                row3[2],
                                row3[5],
                                turn,
                            )
                        ],
                    )
                    newval = list(
                        cur.execute(
                            "SELECT creds FROM polities WHERE polity_id = ?", (row[0],)
                        )
                    )[0][0]
                    cur.execute("DELETE from polities WHERE polity_id = ?", (row[0],))
                    cur.executemany(
                        "INSERT INTO polities VALUES(?, ?, ?, ?)",
                        [
                            (
                                row[0],
                                row[1],
                                row[2],
                                newval + (bp * coefpop),
                            )
                        ],
                    )
                    for row4 in builds:
                        cur.executemany(
                            "DELETE from buildings where planet = ? and building = ? and turns_remains = ? and id = ?",
                            [
                                (
                                    row2[1],
                                    row4[0],
                                    row4[1],
                                    row4[2],
                                )
                            ],
                        )
                        turns = row4[1]
                        if turns > 0:
                            turns = turns - 1
                            newval2 = list(
                                cur.execute(
                                    "SELECT creds FROM polities WHERE polity_id = ?",
                                    (row[0],),
                                )
                            )[0][0]
                            cur.execute(
                                "DELETE from polities WHERE polity_id = ?", (row[0],)
                            )
                            cur.executemany(
                                "INSERT INTO polities VALUES(?, ?, ?, ?)",
                                [
                                    (
                                        row[0],
                                        row[1],
                                        row[2],
                                        newval2
                                        - Buildings.costfetch(Buildings, row4[0]),
                                    )
                                ],
                            )
                        cur.executemany(
                            "INSERT INTO buildings VALUES(?, ?, ?, ?)",
                            [(row2[1], row4[0], turns, row4[2])],
                        )
                station = list(
                    cur.execute(
                        "SELECT station, turns_remains from stations where system = ?",
                        (row2[0],),
                    )
                )
                if len(station) > 0:
                    turns2 = station[0][1]
                    if turns2 > 0:
                        turns2 = turns2 - 1
                        cur.execute("DELETE from stations where system = ?", (row2[0],))
                        cur.executemany(
                            "INSERT INTO stations VALUES(?, ?, ?)",
                            [
                                (
                                    row2[0],
                                    station[0][0],
                                    turns2,
                                )
                            ],
                        )
        calc_pop()
        calc_transfer()
        con.commit

        return DiscordStatusCode.all_clear

    @classmethod
    def fetch_Planet(cls, pln):
        if not check_table():
            return None, None, DiscordStatusCode.no_table
        plsys = list(cur.execute("SELECT system FROM systems where planet = ?", (pln,)))
        if len(plsys) == 0:
            return None, None, DiscordStatusCode.no_elem
        planetsystem = plsys[0][0]
        planetresources = list(
            cur.execute(
                "SELECT RO, BP, GP, VP, RS, pop FROM resources where planet = ?", (pln,)
            )
        )[0]
        return planetsystem, planetresources, DiscordStatusCode.all_clear

    @classmethod
    def fetch_System(cls, sys):
        if not check_table():
            return None, None, None, DiscordStatusCode.no_table
        plsys = list(cur.execute("SELECT system FROM systems where system = ?", (sys,)))
        if len(plsys) == 0:
            return None, None, None, DiscordStatusCode.no_elem
        planetlist = list(
            cur.execute("SELECT planet FROM systems where system = ?", (sys,))
        )
        sst = ""
        sl = list(
            cur.execute(
                "SELECT station, turns_remains from stations where system = ?", (sys,)
            )
        )
        if len(sl) > 0 and sl[0][1] > 0:
            sst = f"В системе есть строящаяся станция, до завершения {sl[0][1]} ходов."
        elif len(sl) > 0 and sl[0][1] == 0:
            sst = "В системе есть станция."
        planetstring = comma_stringer(planetlist)
        polity = list(
            cur.execute(
                "SELECT polity_name FROM polities where polity_id = ?",
                (
                    list(
                        cur.execute(
                            "SELECT polity_id FROM systems where system = ?", (sys,)
                        )
                    )[0][0],
                ),
            )
        )[0][0]
        return polity, planetstring, sst, DiscordStatusCode.all_clear

    @classmethod
    def fetch_Polity(cls, pol):
        if not check_table():
            return None, None, DiscordStatusCode.no_table
        plsys = list(
            cur.execute("SELECT polity_id FROM polities where polity_name = ?", (pol,))
        )
        if len(plsys) == 0:
            return None, None, DiscordStatusCode.no_elem
        systemlist = list(
            cur.execute(
                "SELECT DISTINCT system from systems where polity_id = ?", (plsys[0])
            )
        )
        systemstring = comma_stringer(systemlist)
        creds = list(
            cur.execute("SELECT creds FROM polities where polity_id = ?", (plsys[0]))
        )[0][0]
        return creds, systemstring, DiscordStatusCode.all_clear

    @classmethod
    def add_BP(cls, pln, rsrs):
        if not check_table():
            return DiscordStatusCode.no_table
        if (
            len(
                list(cur.execute("SELECT system FROM systems where planet = ?", (pln,)))
            )
            == 0
        ):
            return DiscordStatusCode.no_elem
        planetresources = list(
            cur.execute(
                "SELECT RO, BP, RS, GP, VP, pop FROM resources where planet = ?", (pln,)
            )
        )
        cur.execute("DELETE from resources WHERE planet = ?", (pln,))
        cur.executemany(
            "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?)",
            [
                (
                    pln,
                    planetresources[0][0],
                    rsrs,
                    planetresources[0][3],
                    planetresources[0][4],
                    planetresources[0][2],
                    planetresources[0][6],
                )
            ],
        )
        con.commit()
        return DiscordStatusCode.all_clear

    @classmethod
    def transfer_System(cls, sys, pol):
        if not check_table():
            return None, DiscordStatusCode.no_table
        plsys = list(
            cur.execute("SELECT polity_id FROM systems where system = ?", (sys,))
        )
        plname = list(
            cur.execute(
                "SELECT polity_name FROM polities where polity_id = ?", plsys[0]
            )
        )
        if len(plsys) == 0:
            return None, DiscordStatusCode.no_elem
        plpol = list(
            cur.execute("SELECT polity_id FROM polities where polity_name = ?", (pol,))
        )
        if len(plpol) == 0:
            return None, None, DiscordStatusCode.no_elem
        if plsys == plpol:
            return None, None, DiscordStatusCode.invalid_elem
        systemlist = list(
            cur.execute("SELECT planet FROM systems where system = ?", (sys,))
        )
        cur.executemany(
            "DELETE from systems where polity_id = ? AND system = ?",
            [
                (
                    plsys[0][0],
                    sys,
                )
            ],
        )
        for system in systemlist:
            cur.executemany(
                "INSERT INTO systems VALUES(?, ?, ?)",
                [
                    (
                        plpol[0][0],
                        sys,
                        system[0],
                    )
                ],
            )
        con.commit()
        return plname[0][0], DiscordStatusCode.all_clear

    @classmethod
    def create_planet(cls, sys, pln):
        if not check_table():
            return DiscordStatusCode.no_table
        if (
            len(
                list(cur.execute("SELECT planet from systems where planet = ?", (pln,)))
            )
            != 0
        ):
            return DiscordStatusCode.redundant_elem
        if (
            len(
                list(cur.execute("SELECT system from systems where system = ?", (sys,)))
            )
            != 0
        ):
            return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO unclaimed_systems VALUES(?, ?)",
            [
                (
                    sys,
                    pln,
                )
            ],
        )
        cur.executemany(
            "INSERT INTO unclaimed_planets VALUES(?, ?, ?, ?, ?)",
            [(pln, 0.0, 0.0, 0.0, 0.0)],
        )
        con.commit()
        return DiscordStatusCode.all_clear

    @classmethod
    def claim_system(cls, plt, sys):
        if not check_table():
            return DiscordStatusCode.no_table
        plt_id = list(
            cur.execute("SELECT polity_id from polities where polity_name = ?", (plt,))
        )
        if len(plt_id) == 0:
            return DiscordStatusCode.no_elem
        else:
            polid = plt_id[0][0]
        planets = list(
            cur.execute("SELECT planet from unclaimed_systems WHERE system = ?", (sys,))
        )
        if len(planets) == 0:
            return DiscordStatusCode.no_elem
        for planet in planets:
            cur.executemany(
                "INSERT INTO systems VALUES(?, ?, ?)",
                [
                    (
                        polid,
                        sys,
                        planet[0],
                    )
                ],
            )
            ro = random.randint(4, 15)
            cur.executemany(
                "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        planet[0],
                        ro,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                    )
                ],
            )
            cur.execute("DELETE FROM unclaimed_planets WHERE planet = ?", planet)
        cur.execute("DELETE from unclaimed_systems WHERE system = ?", (sys,))
        con.commit
        return DiscordStatusCode.all_clear

    @classmethod
    def build_Building(cls, pln, building):
        if not check_table():
            return DiscordStatusCode.no_table
        flag, time = Buildings.buildingcheck(Buildings, building)
        if not flag:
            return DiscordStatusCode.invalid_elem
        planet = list(
            cur.execute("SELECT planet from systems where planet = ?", (pln,))
        )
        if len(planet) == 0:
            return DiscordStatusCode.no_elem
        oldbuildings = list(
            cur.execute("SELECT building from buildings where planet = ?", (pln,))
        )
        n = 0
        for oldbuilding in oldbuildings:
            if oldbuilding[0] == building:
                n += 1
            if n == Buildings.buildingfetch(Buildings, oldbuilding[0]):
                return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO buildings VALUES(?, ?, ?, ?)",
            [
                (
                    pln,
                    building,
                    time,
                    (n + 1),
                )
            ],
        )
        con.commit()
        return DiscordStatusCode.all_clear

    @classmethod
    def planet_Buildings(cls, pln):
        if not check_table():
            return None, DiscordStatusCode.no_table
        buildingslist = list(
            cur.execute(
                "SELECT building, turns_remains from buildings where planet = ?", (pln,)
            )
        )
        if len(buildingslist) == 0:
            return None, DiscordStatusCode.no_elem
        return buildingslist, DiscordStatusCode.all_clear

    @classmethod
    def build_Station(cls, sys):
        if not check_table():
            return DiscordStatusCode.no_table
        ssystem = list(
            cur.execute("SELECT system from systems where system = ?", (sys,))
        )
        if len(ssystem) == 0:
            return DiscordStatusCode.no_elem
        station = list(
            cur.execute(
                "SELECT station, turns_remains from stations where system = ?", (sys,)
            )
        )
        if len(station) > 0:
            return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO stations VALUES(?, ?, ?)",
            [
                (
                    sys,
                    "station",
                    3,
                )
            ],
        )
        con.commit
        return DiscordStatusCode.all_clear

    @classmethod
    def planet_demos(cls, pln):
        if not check_table():
            return None, None, None, DiscordStatusCode.no_table
        planet = list(
            cur.execute(
                "SELECT RO, BP, GP, VP, RS, pop FROM resources WHERE planet = ?", (pln,)
            )
        )
        if len(planet) == 0:
            return None, None, None, DiscordStatusCode.no_elem
        info = list(
            cur.execute(
                "SELECT RO, BP, GP, VP, RS, pop FROM historical_planet WHERE planet =? ORDER BY turn",
                (pln,),
            )
        )
        if len(info) == 0:
            return None, None, None, DiscordStatusCode.invalid_elem
        bf = []
        stl = []
        for i in range(len(info)):
            if i == (len(info) - 5) and len(info) > 5:
                bf = [
                    info[i][0],
                    info[i][1],
                    info[i][2],
                    info[i][3],
                    info[i][4],
                    info[i][5],
                ]
            if i == (len(info) - 1):
                stl = [
                    info[i][0],
                    info[i][1],
                    info[i][2],
                    info[i][3],
                    info[i][4],
                    info[i][5],
                ]
        return bf, stl, planet[0], DiscordStatusCode.all_clear

    @classmethod
    def polity_finances(cls, plt):
        if not check_table():
            return None, None, None, DiscordStatusCode.no_table
        planet = list(
            cur.execute(
                "SELECT polity_id, polity_desc, creds FROM polities WHERE polity_name = ?",
                (plt,),
            )
        )[0]
        if len(planet) == 0:
            return None, None, None, DiscordStatusCode.no_elem
        info = list(
            cur.execute(
                "SELECT polity_id, polity_desc, creds FROM historical_polity WHERE polity_name =? ORDER BY turn",
                (plt,),
            )
        )
        if len(info) == 0:
            return None, None, None, DiscordStatusCode.invalid_elem
        bf = -100000.0
        stl = -100000.0
        for i in range(len(info)):
            if i == (len(info) - 5) and len(info) > 5:
                bf = info[i][2]
            if i == (len(info) - 1):
                stl = info[i][2]
        return bf, stl, planet[2], DiscordStatusCode.all_clear

    @classmethod
    def deport(cls, pln_1, pln_2):
        if not check_table():
            return DiscordStatusCode.no_table
        pl1pol = list(
            cur.execute("SELECT polity_id from systems where planet = ?", (pln_1,))
        )
        pl2pol = list(
            cur.execute("SELECT polity_id from systems where planet = ?", (pln_2,))
        )
        if len(pl1pol) == 0 or len(pl2pol) == 2:
            return DiscordStatusCode.no_elem
        if pl1pol != pl2pol:
            return DiscordStatusCode.invalid_elem
        for e in list(
            cur.execute(
                "SELECT planetto from population_transfers where planetfrom = ?",
                (pln_1,),
            )
        ):
            if e[0] == pln_2:
                return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO population_transfers VALUES(?, ?)",
            [
                (
                    pln_1,
                    pln_2,
                )
            ],
        )
        con.commit
        return DiscordStatusCode.all_clear

    @classmethod
    def agree(cls, pol_1, pol_2):
        if not check_table():
            return DiscordStatusCode.no_table
        ids = []
        for pol in [pol_1, pol_2]:
            p = list(
                cur.execute(
                    "SELECT polity_id from polities where polity_name = ?",
                    (pol,),
                ),
            )
            if len(p[0]) == 0:
                return DiscordStatusCode.no_elem
            ids.append(p[0][0])
        cur.executemany(
            "INSERT INTO agreements VALUES(?, ?)",
            [
                (
                    ids[0],
                    ids[1],
                )
            ],
        )
        cur.executemany(
            "INSERT INTO agreements VALUES(?, ?)",
            [
                (
                    ids[1],
                    ids[0],
                )
            ],
        )
        con.commit()
        return DiscordStatusCode.all_clear
