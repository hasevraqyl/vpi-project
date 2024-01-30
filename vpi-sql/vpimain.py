import sqlite3
from enum_implement import DiscordStatusCode
from techs import Buildings
from techs import Techs
import numpy as np
import random
import tomllib

random.seed()
with open("migrations.toml", mode="rb") as fp:
    info = tomllib.load(fp)

con = sqlite3.connect("vpi.db")
cur = con.cursor()


def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


"deprecated function? methinks?"


def rand_percent(arg):
    if 0 >= arg:
        return False
    if 1 <= arg:
        return True
    if random.randint(0, 100) <= arg:
        return True
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


"note to self: replace with a function that checks all tables"


def check_table():
    r = cur.execute("SELECT name from sqlite_master WHERE name = 'systems'")
    if r.fetchone() is None:
        print("таблицы нету")
        return False
    return True


"possibly deprecated, possibly will be brought in later, donotdelete"


def calculate_bp(bp_total, b):
    if b[0] == "Основные промзоны" and b[1] == 0:
        bp_total = bp_total + 3.0
    return bp_total


def calculate_vp(vp_total, b):
    if b[0] == "ВПК" and b[1] == 0:
        vp_total = vp_total + 3.0
    return vp_total


def calculate_housing(bs):
    total_housing = 0.0
    housing = ["Кварталы I", "Кварталы II", "Кварталы III", "Трущобы"]
    if not isinstance(bs[0], list):
        builds = []
        builds.append(bs)
    else:
        builds = bs
    for b in builds:
        if b[0] in housing and b[1] == 0:
            total_housing = total_housing + 1.0
    return total_housing


def calculate_space(builds):
    total_space = 0.0
    for b in builds:
        if b[0] == "Зоны" and b[1] == 0:
            total_space = total_space + 1.0
    return total_space


def calculate_academics(b):
    science_output = 0.0
    if b[0] == "Академия" and b[1] == 0:
        science_output = 0.2
    return science_output


"""temporary function"""

"actually i can finally begin working on this one properly"
"it is not done yet!!!!"


def calculate_employment(bs):
    em = 0.0
    if not isinstance(bs[0], list):
        builds = []
        builds.append(bs)
    else:
        builds = bs
    for b in builds:
        if b[0] == "Академия" and b[1] == 0:
            em = em + 1.0
    return em


"this function calculates the status of tech research"


def calc_wearing(builds):
    for b in builds:
        if b[0] == "Кварталы I" and b[1] == 0:
            if rand_percent(2):
                cur.execute(
                    "UPDATE buildings SET building = 'Трущобы' WHERE building = ? and id = ?",
                    (b[0], b[2]),
                )
    con.commit()
    return


def calc_tech(pol):
    techs = cur.execute(
        "SELECT tech_name, cost_left, currently_researched from techs WHERE polity_id = ?",
        (pol,),
    ).fetchall()
    pol_science = cur.execute(
        "SELECT science from polities WHERE polity_id = ?", (pol,)
    ).fetchone()
    for tech in techs:
        if tech[2] == 1:
            newstat = 1
            newcost = tech[1] - pol_science[0]
            if newcost < 0:
                newcost = 0
                newstat = 0
            cur.execute(
                "DELETE FROM techs WHERE tech_name = ? AND polity_id = ?",
                (
                    tech[0],
                    pol,
                ),
            )
            cur.executemany(
                "INSERT INTO techs VALUES(?, ?, ?, ?)",
                [
                    (
                        pol,
                        tech[0],
                        newcost,
                        newstat,
                    )
                ],
            )
            con.commit()
            return
    return


"this function calculates the population after voluntary migration"


def calc_pop():
    li = list(cur.execute("SELECT polity_1, polity_2 from agreements"))
    agrl = []
    for e in li:
        if len(agrl) > 0:
            for zone in agrl:
                if e[0] in zone and e[1] not in zone:
                    zone.append(e[1])
                elif e[0] not in zone and e[1] not in zone:
                    agrl.append([e[0], e[1]])
        else:
            agrl.append([e[0], e[1]])
    plt_list = list(cur.execute("SELECT polity_id from polities"))
    for e in plt_list:
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
                builds = list(
                    cur.execute(
                        """SELECT building, turns_remains, id from buildings WHERE planet = ?""",
                        (planet),
                    )
                )
                """
                promz = len(
                    list(
                        cur.execute(
                            ""SELECT building from buildings WHERE building = 'Основные промзоны' AND planet = ?"",
                            (planet),
                        )
                    )
                )
                """
                "this might also be deprecated?"
                jobs = res[1] + res[2] + res[3] + res[4]
                "+ promz * 3"
                total = (
                    calculate_housing(builds) * 5 + jobs + calculate_employment(builds)
                )
                pops.append(res[0])
                array.append(total)
        s = sum(array)
        for i in range(len(array)):
            array[i] = array[i] / s
        eq = np.multiply(np.array(array), np.array(sum(pops)))
        newpop = []
        for i in range(len(pops)):
            newpop.append(pops[i] * 0.9 + eq[i] * 0.1)
        for i in range(len(planets)):
            cur.execute(
                "UPDATE resources SET pop = ? WHERE planet = ?",
                (newpop[i], planets[i][0]),
            )
    con.commit()
    return


"this function calculates the population after forced transfers"


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
            creds = list(
                cur.execute("SELECT creds from polities WHERE polity_id = ?", sys1[0])
            )[0][0]
            cur.execute(
                "UPDATE polities SET creds = ? WHERE id = ?",
                (
                    (creds - 10),
                    sys1[0][0],
                ),
            )
        frompop = list(
            cur.execute("SELECT pop from resources WHERE planet = ?", (e[0],))
        )[0][0]
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
        topop = list(
            cur.execute("SELECT pop from resources WHERE planet = ?", (e[1],))
        )[0][0]
        topop = topop + transfer
        cur.execute("UPDATE resources SET pop = ? WHERE planet = ?", (e[0],))
        cur.execute("UPDATE resources SET pop = ? WHERE planet = ?", (e[1],))
    con.commit()
    return


class Game(object):
    """@classmethod
    def debug_pop(cls):
        calc_pop()
     @classmethod
     def calculate_ql(cls, pln):
        "currently deprecated, will be rewritten"
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
        return ql, DiscordStatusCode.all_clear"""

    "this function restarts the game from a clean slate"

    @classmethod
    def rollback(cls):
        print("откачено!!!!!!")
        cur.executescript(info.get("rollback"))
        cur.executescript(info.get("migration_prime"))
        polities = [
            (1, "pogglia", "no sex", 0.0, 0.0, 0.0),
            (2, "ubia", "sex", 0.0, 0.0, 0.0),
        ]
        cur.executemany("INSERT INTO polities VALUES(?, ?, ?, ?, ?, ?)", polities)
        resources = [
            ("moskvabad", 12.0, 7.0, 1.0, 1.0, 0.0, 10.0, 1),
            ("rashidun", 12.0, 3.0, 1.0, 1.0, 0.0, 5.0, 1),
            ("zumbia", 20.0, 4.0, 1.0, 1.0, 0.0, 10.0, 1),
            ("ubia", 11.0, 6.0, 1.0, 1.0, 0.0, 4.0, 1),
        ]
        cur.executemany(
            "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?, ?)", resources
        )
        planets = [
            (1, "poggl-loire", "moskvabad", 1),
            (1, "poggl-loire", "rashidun", 1),
            (2, "ub-burgundy", "zumbia", 1),
            (2, "ub-burgundy", "ubia", 1),
        ]
        cur.executemany("INSERT INTO systems VALUES(?, ?, ?, ?)", planets)

        con.commit
        return DiscordStatusCode.all_clear

    "this function makes a new turn (more comments to come)"

    @classmethod
    def turn(cls):
        if not check_table():
            return DiscordStatusCode.no_table
        for row in list(
            cur.execute(
                "SELECT polity_id, polity_name, polity_desc, creds, science, limit_pol FROM polities"
            )
        ):
            academics = 0.0
            turnpol = list(
                cur.execute(
                    "SELECT MAX(turn) from historical_polity where polity_id = ?",
                    (row[0],),
                )
            )[0][0]
            if turnpol is None:
                turnpol = 1
            cur.executemany(
                "INSERT INTO historical_polity VALUES(?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        turnpol,
                        row[4],
                        row[5],
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
                        "SELECT RO, BP, RS, GP, VP, pop, hosp FROM resources WHERE planet = ?",
                        (row2[1],),
                    )
                ):
                    employment = 0.0
                    housing = 0.0
                    bp_total = row3[1]
                    vp_total = row3[4]
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
                    for row4 in list(
                        cur.execute(
                            "select building, turns_remains, id from buildings where planet = ?",
                            (row2[1],),
                        )
                    ):
                        turns = row4[1]
                        if turns > 0:
                            turns = turns - 1
                            newval2 = list(
                                cur.execute(
                                    "SELECT creds FROM polities WHERE polity_id = ?",
                                    (row[0],),
                                )
                            )[0][0]
                            academics = academics + calculate_academics(row4)
                            employment = employment + calculate_employment(row4)
                            housing = housing + calculate_housing(row4)
                            bp_total = calculate_bp(bp_total)
                            vp_total = calculate_vp(vp_total)
                            cur.execute(
                                "UPDATE polities SET creds = ? WHERE polity_id = ?",
                                (
                                    newval2 - Buildings.costfetch(Buildings, row4[0]),
                                    row[0],
                                ),
                            )
                        cur.execute(
                            "UPDATE buildings SET turns_remains = ? WHERE planet = ? and building = ? and id = ?",
                            (
                                turns,
                                row2[1],
                                row4[0],
                                row4[2],
                            ),
                        )
                    """do note resources are stored in NEGATIVE numbers
                    and converted to positive on the point of access
                    idk why i have to do this it breaks otherwise (actually i now know why nvm)
                    """
                    """coefpop will later be calculated through other means"""
                    coefpop = row3[5] / employment + 0.1
                    if coefpop > 1:
                        coefpop = 1
                    coefhouse = housing / row3[5]
                    coeftotal = coefpop * 0.3 + coefhouse * 0.7
                    rsnew = row3[2] + ((row3[0] - bp_total) * coeftotal)
                    popnew = row3[5] * 1.01
                    cur.execute(
                        "UPDATE resources SET RS = ? WHERE planet = ?",
                        (
                            rsnew,
                            row2[1],
                        ),
                    )
                    cur.execute(
                        "UPDATE resources SET pop = ? WHERE planet = ?",
                        (
                            popnew,
                            row2[1],
                        ),
                    )
                    new_values = list(
                        cur.execute(
                            "SELECT creds, limit_pol FROM polities WHERE polity_id = ?",
                            (row[0],),
                        )
                    )[0]
                    cur.execute(
                        "UPDATE polities SET creds = ? WHERE polity_id = ?",
                        (
                            (new_values[0] + (bp_total * coefpop)),
                            row[0],
                        ),
                    )
                    cur.execute(
                        "UPDATE polities SET limit_pol = ? WHERE polity_id = ?",
                        (
                            (new_values[1] + (vp_total * coefpop)),
                            row[0],
                        ),
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
            cur.execute(
                "UPDATE polities SET science = ? WHERE polity_id = ?",
                (
                    academics,
                    row[0],
                ),
            )
            calc_tech(row[0])
        calc_pop()
        calc_transfer()
        con.commit

        return DiscordStatusCode.all_clear

    "this function fetches information about a planet"

    @classmethod
    def fetch_Planet(cls, pln):
        if not check_table():
            return None, None, DiscordStatusCode.no_table
        pl_sys = list(
            cur.execute("SELECT system FROM systems where planet = ?", (pln,))
        )
        if len(pl_sys) == 0:
            return None, None, DiscordStatusCode.no_elem
        planet_system = pl_sys[0][0]
        planet_resources = list(
            cur.execute(
                "SELECT RO, BP, GP, VP, RS, pop, hosp FROM resources WHERE planet = ?",
                (pln,),
            )
        )[0]
        return planet_system, planet_resources, DiscordStatusCode.all_clear

    "this function fetches information about a system"

    @classmethod
    def fetch_System(cls, sys):
        if not check_table():
            return None, None, None, DiscordStatusCode.no_table
        pl_sys = list(
            cur.execute("SELECT system FROM systems where system = ?", (sys,))
        )
        if len(pl_sys) == 0:
            return None, None, None, DiscordStatusCode.no_elem
        planet_list = list(
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
        planet_string = comma_stringer(planet_list)
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
        return polity, planet_string, sst, DiscordStatusCode.all_clear

    "this function fetches information about a polity"

    @classmethod
    def fetch_Polity(cls, pol):
        if not check_table():
            return None, None, DiscordStatusCode.no_table
        pl_sys = list(
            cur.execute("SELECT polity_id FROM polities where polity_name = ?", (pol,))
        )
        if len(pl_sys) == 0:
            return None, None, DiscordStatusCode.no_elem
        system_list = list(
            cur.execute(
                "SELECT DISTINCT system from systems where polity_id = ?", (pl_sys[0])
            )
        )
        system_string = comma_stringer(system_list)
        creds = list(
            cur.execute("SELECT creds FROM polities where polity_id = ?", (pl_sys[0]))
        )[0][0]
        return creds, system_string, DiscordStatusCode.all_clear

    "possibly deprecated: this function adds basic production to a plent"

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
        cur.execute("UPDATE resources SET BP = ? WHERE planet = ?", (pln,))
        con.commit()
        return DiscordStatusCode.all_clear

    "this function transfers a system from one empire to another"

    @classmethod
    def transfer_System(cls, sys, pol):
        if not check_table():
            return None, DiscordStatusCode.no_table
        pl_sys = list(
            cur.execute("SELECT polity_id FROM systems where system = ?", (sys,))
        )
        pl_name = list(
            cur.execute(
                "SELECT polity_name FROM polities where polity_id = ?", pl_sys[0]
            )
        )
        if len(pl_sys) == 0:
            return None, DiscordStatusCode.no_elem
        pl_pol = list(
            cur.execute("SELECT polity_id FROM polities where polity_name = ?", (pol,))
        )
        if len(pl_pol) == 0:
            return None, None, DiscordStatusCode.no_elem
        if pl_sys == pl_pol:
            return None, None, DiscordStatusCode.invalid_elem
        system_list = list(
            cur.execute("SELECT planet FROM systems where system = ?", (sys,))
        )
        cur.executemany(
            "DELETE from systems where polity_id = ? AND system = ?",
            [
                (
                    pl_sys[0][0],
                    sys,
                )
            ],
        )
        for system in system_list:
            cur.executemany(
                "INSERT INTO systems VALUES(?, ?, ?)",
                [
                    (
                        pl_pol[0][0],
                        sys,
                        system[0],
                    )
                ],
            )
        con.commit()
        return pl_name[0][0], DiscordStatusCode.all_clear

    "this function creates an uninhabited unclaimed planet"

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

    "this function adds an unclaimed system to the empire"

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
                "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        planet[0],
                        ro,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0.0,
                        0,
                    )
                ],
            )
            cur.execute("DELETE FROM unclaimed_planets WHERE planet = ?", planet)
        cur.execute("DELETE from unclaimed_systems WHERE system = ?", (sys,))
        con.commit
        return DiscordStatusCode.all_clear

    "this function starts construction on the planet"

    @classmethod
    def build_Building(cls, pln, building):
        if not check_table():
            return DiscordStatusCode.no_table
        flag, time = Buildings.buildingcheck(Buildings, building)
        if not flag:
            return DiscordStatusCode.invalid_elem
        planet = list(
            cur.execute("SELECT planet, hosp from systems where planet = ?", (pln,))
        )
        if len(planet) == 0:
            return DiscordStatusCode.no_elem
        old_buildings = list(
            cur.execute("SELECT building from buildings where planet = ?", (pln,))
        )
        if building in ["Кварталы I", "Квартал II", "Квартал III", "Трущобы"]:
            if (
                calculate_housing(old_buildings) + 1 > calculate_space(old_buildings)
            ) and planet[0][1] == 0:
                return DiscordStatusCode.redundant_elem
        n = 0
        for old_building in old_buildings:
            if old_building[0] == building:
                n += 1
            if n == Buildings.buildingfetch(Buildings, old_building[0]):
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

    "this function fetches the list of all buildings on the planet (completed or not)"

    @classmethod
    def planet_Buildings(cls, pln):
        if not check_table():
            return None, DiscordStatusCode.no_table
        buildings_list = list(
            cur.execute(
                "SELECT building, turns_remains from buildings where planet = ?", (pln,)
            )
        )
        if len(buildings_list) == 0:
            return None, DiscordStatusCode.no_elem
        return buildings_list, DiscordStatusCode.all_clear

    "this function builds a station in the system"

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

    "this function fetches polity finances over time"

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

    "this function activates a deportation policy"

    @classmethod
    def deport(cls, pln_1, pln_2):
        if not check_table():
            return DiscordStatusCode.no_table
        pln1_pol = list(
            cur.execute("SELECT polity_id from systems where planet = ?", (pln_1,))
        )
        pln2_pol = list(
            cur.execute("SELECT polity_id from systems where planet = ?", (pln_2,))
        )
        if len(pln1_pol) == 0 or len(pln2_pol) == 2:
            return DiscordStatusCode.no_elem
        if pln1_pol != pln2_pol:
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

    "this function begins researching new technology"

    @classmethod
    def research_tech(cls, pol, tech):
        if not check_table():
            return DiscordStatusCode.no_table
        polity = list(
            cur.execute(
                "SELECT polity_id, polity_desc, creds, science from polities where polity_name = ?",
                (pol,),
            )
        )
        if len(polity) == 0:
            return None, DiscordStatusCode.no_elem
        cat_tech, cost_tech, num_tech = Techs.fetch_tech(Techs, tech)
        if cat_tech is None:
            return None, DiscordStatusCode.invalid_elem
        techs = list(
            cur.execute(
                "SELECT tech_name, cost_left, currently_researched from techs where polity_id = ?",
                (polity[0][0],),
            )
        )
        tech_flag = False
        cur_tech = ()
        if num_tech == 1:
            tech_flag = True
        currently_researched = ""
        for tech in techs:
            if tech[0] == tech and (tech[2] == 1 or tech[1] == 0.0):
                return None, DiscordStatusCode.redundant_elem
            cat_oldtech, _, num_oldtech = Techs.fetch_tech(tech[0])
            if cat_oldtech == cat_tech and num_oldtech == num_tech - 1:
                tech_flag = True
            if tech[2] == 1:
                cur_tech = tech
                currently_researched = tech[0]
        if tech_flag:
            if cur_tech != ():
                cur.execute(
                    "DELETE FROM techs WHERE tech_name = ? and polity_id = ?",
                    (cur_tech[0], polity[0][0]),
                )
                cur.executemany(
                    "INSERT INTO techs VALUES(?, ?, ?, ?)",
                    [
                        (
                            polity[0][0],
                            cur_tech[0],
                            cur_tech[1],
                            0,
                        )
                    ],
                )
            cur.execute(
                "DELETE FROM techs where tech_name = ? and polity_id = ?",
                (tech, polity[0][0]),
            )
            cur.executemany(
                "INSERT INTO techs VALUES(?, ?, ?, ?)",
                [
                    (
                        polity[0][0],
                        tech,
                        cost_tech,
                        num_tech,
                    )
                ],
            )
            con.commit()
            return currently_researched, DiscordStatusCode.all_clear
        else:
            return None, DiscordStatusCode.invalid_elem

    "this function creates a common demographic space from two empires"

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
