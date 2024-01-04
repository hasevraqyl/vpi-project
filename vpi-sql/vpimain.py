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
        return False
    return True


class Game(object):
    @classmethod
    def rollback(cls):
        cur.execute("DROP TABLE IF EXISTS polities")
        cur.execute("DROP TABLE IF EXISTS systems")
        cur.execute("DROP TABLE IF EXISTS resources")
        cur.execute("DROP TABLE IF EXISTS buildings")
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
                DEFAULT (0.0) );"""
        )
        resources = [
            ("moskvabad", 12.0, 7.0, 1.0, 1.0, 0.0),
            ("rashidun", 12.0, 3.0, 1.0, 1.0, 0.0),
            ("zumbia", 20.0, 4.0, 1.0, 1.0, 0.0),
            ("ubia", 11.0, 6.0, 1.0, 1.0, 0.0),
        ]
        cur.executemany("INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?)", resources)
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
                        "SELECT RO, BP, RS, GP, VP FROM resources WHERE planet = ?",
                        (row2[1],),
                    )
                ):
                    print("resources stored on planet ", row2[1], ": ", abs(row3[2]))
                    """do note resources are stored in NEGATIVE numbers
                    and converted to positive on the point of access
                    idk why i have to do this it breaks otherwise (actually i now know why nvm)"""
                    rsnew = (
                        row3[2]
                        + (row3[1] - row3[0])
                        + (row3[3] - row3[0])
                        + (row3[4] - row3[0])
                    )
                    cur.execute("DELETE from resources WHERE planet = ?", (row2[1],))
                    cur.executemany(
                        "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?)",
                        [
                            (
                                row2[1],
                                row3[0],
                                row3[1],
                                row3[3],
                                row3[4],
                                rsnew,
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
                                newval + row3[1],
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
                "SELECT RO, BP, GP, VP, RS FROM resources where planet = ?", (pln,)
            )
        )[0]
        return planetsystem, planetresources, DiscordStatusCode.all_clear

    @classmethod
    def fetch_System(cls, sys):
        if not check_table():
            return None, None, DiscordStatusCode.no_table
        plsys = list(cur.execute("SELECT system FROM systems where system = ?", (sys,)))
        if len(plsys) == 0:
            return None, None, DiscordStatusCode.no_elem
        planetlist = list(
            cur.execute("SELECT planet FROM systems where system = ?", (sys,))
        )
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
        return polity, planetstring, DiscordStatusCode.all_clear

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
                "SELECT RO, BP, RS, GP, VP FROM resources where planet = ?", (pln,)
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
        for oldbuilding in oldbuildings:
            if oldbuilding[0] == building:
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
                    f"\n {building[0]}. До окончания постройки {building[0]} ходов."
                )
            else:
                string += f"\n {building[0]}"
        return string, DiscordStatusCode.all_clear
