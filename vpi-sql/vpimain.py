import sqlite3
from enum_implement import DiscordStatusCode
from techs import Buildings

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


class Game(object):
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
    turns_remains INT NOT NULL
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
                            "select building, turns_remains from buildings where planet = ?",
                            (row2[1],),
                        )
                    )
                    coefpop = row3[5] / (abs(row3[0]) + row3[3] + row3[4])
                    if coefpop > 1:
                        coefpop = 1
                    bp = calculate_bp(row3[1], builds)
                    rsnew = row3[2] + ((row3[0] - bp) * coefpop)
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
                                newval + (row3[1] * coefpop),
                            )
                        ],
                    )
                    for row4 in builds:
                        cur.executemany(
                            "DELETE from buildings where planet = ? and building = ? and turns_remains = ?",
                            [
                                (
                                    row2[1],
                                    row4[0],
                                    row4[1],
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
                            "INSERT INTO buildings VALUES(?, ?, ?)",
                            [
                                (
                                    row2[1],
                                    row4[0],
                                    turns,
                                )
                            ],
                        )
                    con.commit()
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
            "INSERT INTO buildings VALUES(?, ?, ?)",
            [
                (
                    pln,
                    building,
                    time,
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
        string = ""
        for building in buildingslist:
            if building[1] != 0:
                string += (
                    f"\n {building[0]}. До окончания постройки {building[1]} ходов."
                )
            else:
                string += f"\n {building[0]}"
        return string, DiscordStatusCode.all_clear

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
        return DiscordStatusCode.all_clear
