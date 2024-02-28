import sqlite3
from enum_implement import DiscordStatusCode
from techs import Buildings
from techs import Techs
from techs import Modules
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


def calculate_bp(b, bp_total):
    if b[0] == "Основные промзоны" and b[1] == 0:
        bp_total = bp_total + 3.0
    return bp_total


def calculate_vp(b, vp_total):
    if b[0] == "ВПК" and b[1] == 0:
        vp_total = vp_total + 3.0
    return vp_total


def calculate_housing(bs):
    total_housing = 0.0
    if len(bs) == 0 or bs is None:
        return total_housing
    if not isinstance(bs[0], tuple):
        builds = []
        builds.append(bs)
    else:
        builds = bs
    for b in builds:
        if Buildings.fetch(b[0]).h and b[1] == 0:
            total_housing += 1.0
    return total_housing


def calculate_space(builds):
    total_space = 0.0
    for b in builds:
        if b[0] == "Зоны" and b[1] == 0:
            total_space += 1.0
    return total_space


def calculate_academics(b):
    science_output = 0.0
    if b[0] == "Академия" and b[1] == 0:
        science_output = 0.2
    return science_output


def calculate_h(b):
    total_h = 0.0
    if b[0] == "Шахта Г" and b[1] == 0:
        total_h = 1.0
    return total_h


def calculate_sh(b):
    if b[0] == "Шахта" and b[1] == 0:
        return 1.0
    return 0


def calculate_s(b):
    total_s = 0.0
    if b[0] == "Шахта С" and b[1] == 0:
        total_s = 1.0
    return total_s


"""temporary function"""

"actually i can finally begin working on this one properly"
"it is not done yet!!!!"
"still not done; reminder that return 0.1 is a temporary measure"


def calculate_employment(bs):
    em = 0.0
    if len(bs) == 0 or bs is None:
        return 0.1
    if not isinstance(bs[0], tuple):
        builds = []
        builds.append(bs)
    else:
        builds = bs
    for b in builds:
        if Buildings.fetch(b[0]).e and b[1] == 0:
            em += 1.0
    return em


"this function calculates the status of tech research"


def calc_wearing(b, pln):
    if b[0] == "Кварталы I" and b[1] == 0:
        if rand_percent(2):
            cur.execute(
                "UPDATE buildings SET building = 'Аварийные кварталы' WHERE building = ? and id = ? and planet = ?",
                (
                    b[0],
                    b[2],
                    pln,
                ),
            )
    con.commit()
    return


def calc_munic(pln):
    mun = list(
        cur.execute(
            "SELECT id, data FROM buildings WHERE planet = ? AND building = 'Муниципалка' AND turns_remains = 0",
            (pln,),
        )
    )
    av = list(
        cur.execute(
            "SELECT id FROM buildings WHERE planet = ? AND building = 'Аварийные кварталы'",
            (pln,),
        )
    )
    t = len(av)
    n = 0
    for m in mun:
        if m[1] == "in_use":
            cur.execute(
                "UPDATE buildings SET data = '' WHERE planet = ? and building = 'Муниципалка' AND id = ?",
                (
                    pln,
                    m[0],
                ),
            )
        elif m[1] == "":
            if n < t:
                cur.execute(
                    "UPDATE buildings SET data = '' WHERE planet = ? and building = 'Муниципалка' and id = ?",
                    (
                        pln,
                        m[0],
                    ),
                )
                cur.execute(
                    "UPDATE buildings SET building = 'Кварталы I' WHERE planet = ? and building = 'Аварийные кварталы' and id = ?",
                    (
                        pln,
                        av[n][0],
                    ),
                )
                n += 1
    con.commit()
    return


def calc_ship(pol):
    for system in cur.execute(
        "SELECT DISTINCT system from systems WHERE polity_id = ?", (pol,)
    ):
        for ship in cur.execute(
            "SELECT limit_ship, ship_id from spaceships WHERE shipyard = ?", system
        ).fetchall():
            if ship[0] < 300:
                cur.execute(
                    "UPDATE spaceships SET limit_ship = ?, shipyard = '' WHERE ship_id = ?",
                    (
                        0,
                        ship[1],
                    ),
                )
                id = cur.execute("SELECT MAX(own_id) from fleets").fetchone()
                cur.executemany(
                    "INSERT into fleets VALUES(?, ?, ?, ?)",
                    [
                        (
                            id + 1,
                            pol,
                            system,
                            system + str(id),
                        )
                    ],
                )
            else:
                cur.execute(
                    "UPDATE spaceships SET limit_ship = ? WHERE ship_id = ?",
                    (
                        ship[0] - 300,
                        ship[1],
                    ),
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
            frompop = -1
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
            (1, "pogglia", "no sex", 0.0, 0.0, 0.0, 0.0, 0.0),
            (2, "ubia", "sex", 0.0, 0.0, 0.0, 0.0, 0.0),
        ]
        cur.executemany("INSERT INTO polities VALUES(?, ?, ?, ?, ?, ?, ?, ?)", polities)
        resources = [
            ("moskvabad", 12.0, 7.0, 1.0, 1.0, 0.0, 10.0, 1, 0.0, 0.0),
            ("rashidun", 12.0, 3.0, 1.0, 1.0, 0.0, 5.0, 1, 0.0, 0.0),
            ("zumbia", 20.0, 4.0, 1.0, 1.0, 0.0, 10.0, 1, 0.0, 0.0),
            ("ubia", 11.0, 6.0, 1.0, 1.0, 0.0, 4.0, 1, 0.0, 0.0),
        ]
        cur.executemany(
            "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", resources
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
                "SELECT polity_id, polity_name, polity_desc, creds, science, limit_pol, limit_hyp, limit_sil FROM polities"
            )
        ):
            calc_ship(row[0])
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
                "INSERT INTO historical_polity VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        row[0],
                        row[1],
                        row[2],
                        row[3],
                        turnpol,
                        row[4],
                        row[5],
                        row[6],
                        row[7],
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
                        "SELECT RO, BP, RS, GP, VP, pop, hosp, hyp, sil FROM resources WHERE planet = ?",
                        (row2[1],),
                    )
                ):
                    employment = 0.0
                    housing = 0.0
                    bp_total = row3[1]
                    vp_total = row3[4]
                    total_h = 0.0
                    total_s = 0.0
                    total_sh = 0.0
                    turn = list(
                        cur.execute(
                            "SELECT MAX(turn) FROM historical_planet where planet = ?",
                            (row2[1],),
                        )
                    )[0][0]
                    if turn is None:
                        turn = 1
                    cur.executemany(
                        "INSERT INTO historical_planet VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        [
                            (
                                row2[1],
                                row3[0],
                                row3[1],
                                row3[3],
                                row3[4],
                                row3[2],
                                row3[5],
                                row3[6],
                                row3[7],
                                turn,
                            )
                        ],
                    )
                    for row4 in list(
                        cur.execute(
                            "select building, turns_remains, id, data from buildings where planet = ?",
                            (row2[1],),
                        )
                    ):
                        turns = row4[1]
                        if turns > 0:
                            turns = turns - 1
                            vr = list(
                                cur.execute(
                                    "SELECT creds, limit_pol FROM polities WHERE polity_id = ?",
                                    (row[0],),
                                )
                            )[0]
                            academics = academics + calculate_academics(row4)
                            employment = employment + calculate_employment(row4)
                            housing = housing + calculate_housing(row4)
                            "the following might be deprecated"
                            bp_total = calculate_bp(row4, bp_total)
                            vp_total = calculate_vp(row4, vp_total)
                            total_h = calculate_h(row4)
                            total_s = calculate_s(row4)
                            total_sh = calculate_sh(row4)
                            calc_wearing(row2[1], row4)
                            bi = Buildings.fetch(row4[0])
                            cur.execute(
                                "UPDATE polities SET creds = ?, limit_pol = ? WHERE polity_id = ?",
                                (
                                    vr[0] - bi.cost,
                                    vr[1] - bi.lim,
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
                    calc_munic(row2[1])
                    cpop = row3[5] / (employment + 0.1)
                    if cpop > 1:
                        cpop = 1
                    chouse = housing / row3[5]
                    ctotal = cpop * 0.3 + chouse * 0.7
                    bp_total = min(bp_total, total_sh)
                    rsnew = min((row3[2] + ((row3[0] - bp_total) * ctotal)), total_sh)
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
                            "SELECT creds, limit_pol, limit_hyp, limit_sil FROM polities WHERE polity_id = ?",
                            (row[0],),
                        )
                    )[0]
                    cur.execute(
                        "UPDATE polities SET creds = ? WHERE polity_id = ?",
                        (
                            (new_values[0] + (bp_total * cpop)),
                            row[0],
                        ),
                    )
                    cur.execute(
                        "UPDATE polities SET limit_pol = ?, limit_hyp = ?, limit_sil = ? WHERE polity_id = ?",
                        (
                            (new_values[1] + (vp_total * cpop)),
                            (new_values[2] + total_h),
                            (new_values[3] + total_s),
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
                        turns2 = -1
                        cur.execute(
                            "UPDATE stations SET turns_remains = ? WHERE system = ?",
                            (
                                turns2,
                                row2[0],
                            ),
                        )
                    for build in list(
                        cur.execute(
                            "SELECT building, turns_remains, id from station_builds WHERE system = ?",
                            (row2[0],),
                        )
                    ):
                        turns3 = build[1]
                        if turns3 > 0:
                            turns3 = turns3 - 1
                            b = Buildings.fetch(build[0])
                            cur.execute(
                                "UPDATE polities SET creds = ?, limit_pol = ? WHERE polity_id = ?",
                                (row[3] - b.cost, row[5] - b.lim, row[0]),
                            )
                            cur.execute(
                                "UPDATE station_builds SET turns_remains = ? WHERE system = ? AND id = ?",
                                (
                                    turns3,
                                    row2[0],
                                    build[2],
                                ),
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
            return None, None, None, None, DiscordStatusCode.no_table
        pl_sys = list(
            cur.execute("SELECT system FROM systems where system = ?", (sys,))
        )
        if len(pl_sys) == 0:
            return None, None, None, None, DiscordStatusCode.no_elem
        planet_list = list(
            cur.execute("SELECT planet FROM systems where system = ?", (sys,))
        )
        sst = 0
        sl = list(
            cur.execute(
                "SELECT station, turns_remains from stations where system = ?", (sys,)
            )
        )
        if len(sl) > 0 and sl[0][1] > 0:
            sst = sl[0][1]
        elif len(sl) > 0 and sl[0][1] == 0:
            sst = 0
        connection_list = cur.execute(
            "SELECT system2 FROM connections WHERE system1 = ?", (sys,)
        ).fetchall()
        planet_string = comma_stringer(planet_list)
        connection_string = comma_stringer(connection_list)
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
        return (
            polity,
            planet_string,
            sst,
            connection_string,
            DiscordStatusCode.all_clear,
        )

    @classmethod
    def fetch_Unclaimed(cls, sys):
        if not check_table():
            return None, DiscordStatusCode.no_table
        pl_sys = list(
            cur.execute("SELECT system FROM unclaimed_systems where system = ?", (sys,))
        )
        if len(pl_sys) == 0:
            return None, DiscordStatusCode.no_elem
        return (
            comma_stringer(
                cur.execute(
                    "SELECT planet FROM unclaimed_systems where system = ?", (sys,)
                ).fetchall()
            ),
            DiscordStatusCode.all_clear,
        )

    "this function fetches information about a polity"

    @classmethod
    def polity_list(cls):
        if not check_table():
            return None, DiscordStatusCode.no_table
        return (
            comma_stringer(list(cur.execute("SELECT polity_name from polities"))),
            DiscordStatusCode.all_clear,
        )

    """unfinished business below; need to research right/left join"""

    @classmethod
    def station_list(cls, pol):
        if not check_table():
            return None, None, DiscordStatusCode.no_table
        pol_id = list(
            cur.execute("SELECT polity_id FROM polities WHERE polity_name = ?", (pol,))
        )
        if len(pol_id) == 0:
            return None, None, DiscordStatusCode.no_elem
        return (
            comma_stringer(
                list(
                    cur.execute(
                        "SELECT DISTINCT systems.system FROM systems INNER JOIN stations ON stations.system = systems.system WHERE stations.turns_remains = 0 AND systems.polity_id = ?",
                        pol_id[0],
                    )
                )
            ),
            comma_stringer(
                list(
                    cur.execute(
                        "SELECT DISTINCT systems.system FROM systems INNER JOIN stations ON stations.system = systems.system WHERE stations.turns_remains != 0 AND systems.polity_id = ?",
                        pol_id[0],
                    )
                )
            ),
            DiscordStatusCode.all_clear,
        )

    @classmethod
    def unclaimed_systems(cls):
        if not check_table():
            return None, DiscordStatusCode.no_table
        return (
            comma_stringer(
                list(cur.execute("SELECT DISTINCT system FROM unclaimed_systems"))
            ),
            DiscordStatusCode.all_clear,
        )

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
    def create_Connection(cls, sys1, sys2):
        if not check_table():
            return DiscordStatusCode.no_table
        for s in [sys1, sys2]:
            if (
                cur.execute(
                    "SELECT DISTINCT system FROM systems WHERE system = ?", (s,)
                ).fetchone()
                is None
                and cur.execute(
                    "SELECT DISTINCT system from unclaimed_systems WHERE system = ?",
                    (s,),
                ).fetchone()
                is None
            ):
                return DiscordStatusCode.no_elem
        if (
            cur.execute(
                "SELECT system1 FROM connections WHERE system1 = ? AND system2 = ?",
                (
                    sys1,
                    sys2,
                ),
            ).fetchone()
            or cur.execute(
                "SELECT system1 FROM unclaimed_connections WHERE system1 = ? AND system2 = ?",
                (
                    sys1,
                    sys2,
                ),
            ).fetchone()
        ) is not None:
            return DiscordStatusCode.redundant_elem
        if (
            cur.execute(
                "SELECT DISTINCT system FROM systems wHERE system = ?", (sys1,)
            ).fetchone()
            is not None
        ):
            print("got here 2")
            cur.executemany(
                "INSERT INTO connections VALUES(?, ?)",
                [
                    (
                        sys1,
                        sys2,
                    )
                ],
            )
        else:
            print("got here 3")
            cur.executemany(
                "INSERT INTO unclaimed_connections VALUES(?, ?)",
                [
                    (
                        sys1,
                        sys2,
                    )
                ],
            )
        if (
            cur.execute(
                "SELECT DISTINCT system FROM systems wHERE system = ?", (sys2,)
            ).fetchone()
            is not None
        ):
            cur.executemany(
                "INSERT INTO connections VALUES(?, ?)",
                [
                    (
                        sys2,
                        sys1,
                    )
                ],
            )
        else:
            cur.executemany(
                "INSERT INTO unclaimed_connections VALUES(?, ?)",
                [
                    (
                        sys2,
                        sys1,
                    )
                ],
            )
        con.commit()
        return DiscordStatusCode.all_clear

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

    @classmethod
    def generate_system(cls, sys):
        if not check_table():
            return DiscordStatusCode.no_table
        if (
            cur.execute(
                "SELECT system from systems where system = ?", (sys,)
            ).fetchone()
            is not None
        ):
            return DiscordStatusCode.redundant_elem
        b = rand_percent(10)
        pl = 8
        if b:
            pl = 7
            cur.executemany(
                "INSERT INTO unclaimed_systems VALUES(?, ?)",
                [
                    (
                        sys,
                        f"{sys} 1",
                    )
                ],
            )
            x = rand_percent(3)
            y = rand_percent(10)
            hyp = 0.0
            sil = 0.0
            if x:
                hyp = float(random.randint(0, 2))
            if y:
                sil = float(random.randint(0, 3))
            cur.executemany(
                "INSERT INTO unclaimed_planets VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        f"{sys} 1",
                        float(random.randint(0, 20)),
                        0.0,
                        0.0,
                        0.0,
                        hyp,
                        sil,
                        1,
                    )
                ],
            )
        for i in range(random.randint(0, pl)):
            if b:
                name = f"{sys} {i+2}"
            else:
                name = f"{sys} {i+1}"
            cur.executemany(
                "INSERT INTO unclaimed_systems VALUES(?, ?)",
                [
                    (
                        sys,
                        name,
                    )
                ],
            )
            x = rand_percent(3)
            y = rand_percent(10)
            hyp = 0.0
            sil = 0.0
            if x:
                hyp = float(random.randint(0, 2))
            if y:
                sil = float(random.randint(0, 3))
            cur.executemany(
                "INSERT INTO unclaimed_planets VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        name,
                        float(random.randint(0, 20)),
                        0.0,
                        0.0,
                        0.0,
                        hyp,
                        sil,
                        0,
                    )
                ],
            )
        con.commit()
        return DiscordStatusCode.all_clear

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
        plt_id = cur.execute(
            "SELECT polity_id FROM polities WHERE polity_name = ?", (plt,)
        ).fetchone()
        if plt_id is None:
            return DiscordStatusCode.no_elem
        planets = cur.execute(
            "SELECT planet FROM unclaimed_systems WHERE system = ?", (sys,)
        ).fetchall()
        if len(planets) == 0:
            return DiscordStatusCode.no_elem
        for planet in planets:
            res = cur.execute(
                "SELECT RO, BP, GP, VP, hyp, sil, hosp FROM unclaimed_planets WHERE planet = ?",
                planet,
            ).fetchall()
            cur.executemany(
                "INSERT INTO resources VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (
                        planet[0],
                        res[0],
                        res[1],
                        res[2],
                        res[3],
                        0.0,
                        res[4],
                        res[5],
                        res[6],
                    )
                ],
            )
            cur.executemany(
                "INSERT INTO systems VALUES(?, ?, ?)", [(plt_id, sys, planet[0])]
            )
            cur.execute("DELETE FROM unclaimed_planets WHERE planet = ?", planet)
            cur.execute("DELETE FROM unclaimed_systems WHERE planet = ?", planet)
        cn = cur.execute(
            "SELECT system2 FROM unclaimed_connections WHERE system1 = ?", (sys,)
        ).fetchall()
        for c in cn:
            cur.executemany(
                "INSERT INTO connections VALUES(?, ?)",
                [
                    (
                        sys,
                        c[0],
                    )
                ],
            )
        cur.execute("DELETE FROM unclaimed_systems WHERE system = ?", (sys,))
        cur.execute("DELETE FROM unclaimed_connections WHERE system1 = ?", (sys,))
        con.commit()
        return DiscordStatusCode.all_clear

    "this function starts construction on the planet"

    @classmethod
    def build_Building(cls, pln, building):
        if not check_table():
            return DiscordStatusCode.no_table
        b = Buildings.fetch(building)
        time = b.buildtime
        if b is None or b.b:
            return DiscordStatusCode.invalid_elem
        planet = list(
            cur.execute(
                "SELECT planet, hosp, hyp, sys, RO from systems where planet = ?",
                (pln,),
            )
        )[0]
        if len(planet) == 0:
            return DiscordStatusCode.no_elem
        old_buildings = list(
            cur.execute(
                "SELECT building, turns_remains, id from buildings where planet = ?",
                (pln,),
            )
        )
        if b.h:
            if (
                calculate_housing(old_buildings) + 1 > calculate_space(old_buildings)
            ) and planet[1] == 0:
                return DiscordStatusCode.redundant_elem
        n = 0
        for old_building in old_buildings:
            if old_building[0] == building:
                n += 1
            if n == Buildings.fetch(old_building[0]).maxi:
                return DiscordStatusCode.redundant_elem
            if building == "Шахта Г" and n == planet[2]:
                return DiscordStatusCode.redundant_elem
            if building == "Шахта С" and n == planet[3]:
                return DiscordStatusCode.redundant_elem
            if building == "Шахта" and n == planet[4]:
                return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO buildings VALUES(?, ?, ?, ?, ?)",
            [
                (
                    pln,
                    building,
                    time,
                    (n + 1),
                    "",
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
            cur.execute("SELECT system FROM systems WHERE system = ?", (sys,))
        )
        if len(ssystem) == 0:
            return DiscordStatusCode.no_elem
        station = list(
            cur.execute(
                "SELECT station, turns_remains FROM stations WHERE system = ?", (sys,)
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
    def improve_Station(cls, sys, building):
        if not check_table():
            return DiscordStatusCode.no_table
        ssystem = list(
            cur.execute("SELECT system FROM systems WHERE system = ?", (sys,))
        )
        if len(ssystem) == 0:
            return DiscordStatusCode.no_elem
        station = list(
            cur.execute(
                "SELECT station, turns_remains FROM stations WHERE system = ?", (sys,)
            )
        )
        if len(station) == 0:
            return DiscordStatusCode.no_elem
        if station[0][1] != 0:
            return DiscordStatusCode.no_elem
        old_buildings = list(
            cur.execute(
                "SELECT building, turns_remains, id from station_builds where system = ? AND building = ?",
                (
                    sys,
                    building,
                ),
            )
        )
        b = Buildings.fetch(building)
        n = len(old_buildings)
        if n >= b.maxi:
            return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO station_builds VALUES(?, ?, ?, ?, ?)",
            [
                (
                    sys,
                    building,
                    b.buildtime,
                    (n + 1),
                    "",
                )
            ],
        )
        con.commit()
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
        bf = -1000000000.0
        stl = -1000000000.0
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
        t = Techs.fetch(tech)
        if t.category is None:
            return None, DiscordStatusCode.invalid_elem
        techs = list(
            cur.execute(
                "SELECT tech_name, cost_left, currently_researched from techs where polity_id = ?",
                (polity[0][0],),
            )
        )
        tech_flag = False
        cur_tech = ()
        if t.number == 1:
            tech_flag = True
        currently_researched = ""
        for tech in techs:
            if tech[0] == tech and (tech[2] == 1 or tech[1] == 0.0):
                return None, DiscordStatusCode.redundant_elem
            ot = Techs.fetch(tech[0])
            if ot.category == t.category and ot.number == t.number - 1:
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
                        t.cost,
                        t.number,
                    )
                ],
            )
            con.commit()
            return currently_researched, DiscordStatusCode.all_clear
        else:
            return None, DiscordStatusCode.invalid_elem

    @classmethod
    def build_Ship(cls, name, tmpl, sys):
        if not check_table():
            return DiscordStatusCode.no_table
        pol_id = list(
            cur.execute("SELECT polity_id FROM systems WHERE system = ?", (sys,))
        )[0][0]
        sya = len(
            list(
                cur.execute(
                    "SELECT id FROM station_builds WHERE building = 'Верфь' and system = ? and turns_remains = 0",
                    (sys,),
                )
            )
        )
        ships = len(
            list(
                cur.execute("SELECT ship_id FROM spaceships WHERE shipyard = ?", (sys,))
            )
        )
        if ships >= sya:
            return DiscordStatusCode.redundant_elem
        t = list(
            cur.execute(
                "SELECT cost FROM templates WHERE name = ? AND polity_id = ?",
                (
                    tmpl,
                    pol_id,
                ),
            )
        )
        id = (
            list(cur.execute((cur.execute("SELECT MAX(id) FROM spaceships"))))[0][0] + 1
        )
        cur.executemany(
            "INSERT INTO spaceships VALUES(?, ?, ?, ?)",
            [
                (
                    0,
                    id,
                    t,
                    sys,
                )
            ],
        )
        con.commit()
        return DiscordStatusCode.all_clear

    @classmethod
    def build_module(cls, pol, name, tmpl):
        if not check_table():
            return DiscordStatusCode.no_table
        pol_id = list(
            cur.execute("SELECT polity_id FROM polities WHERE polity_name = ?"), (pol,)
        )[0][0]
        if pol_id is None:
            return DiscordStatusCode.no_elem
        costid = list(
            cur.execute(
                "SELECT cost, id FROM templates WHERE polity_id = ? AND name = ?",
                (
                    pol_id,
                    tmpl,
                ),
            )
        )[0]
        if costid[0] is None:
            return DiscordStatusCode.no_elem
        mod = Modules.fetch(name)
        if mod is None:
            return DiscordStatusCode.invalid_elem
        totalcost = 0
        for c in list(
            cur.execute(
                "SELECT type FROM template_modules WHERE name = ? AND id = ?",
                (
                    tmpl,
                    costid[1],
                ),
            )
        ):
            totalcost += Modules.fetch(c[0]).cost
        if totalcost > costid[0]:
            return DiscordStatusCode.redundant_elem
        cur.executemany(
            "INSERT INTO template_modules VALUES(?, ?, ?)",
            [
                (
                    tmpl,
                    costid[1],
                    name,
                )
            ],
        )
        con.commit()
        return DiscordStatusCode.all_clear

    "this function creates a common demographic space from two empires"

    @classmethod
    def build_Template(cls, pol, name, cost):
        if not check_table():
            return DiscordStatusCode.no_table
        pol_id = list(
            cur.execute("SELECT polity_id FROM polities WHERE polity_name = ?", (pol,))
        )[0][0]
        if pol_id is None:
            return DiscordStatusCode.no_elem
        templ = list(
            cur.execute(
                "SELECT name FROM templates WHERE polity_id = ? AND name = ?",
                (
                    pol_id,
                    name,
                ),
            )
        )
        if len(templ) != 0:
            return DiscordStatusCode.redundant_elem
        mx = cur.execute("SELECT max(id) FROM templates").fetchone()[0]
        if mx is None:
            mx = 0
        cur.executemany(
            "INSERT INTO templates VALUES(?, ?, ?, ?)",
            [
                (
                    pol_id,
                    name,
                    cost,
                    mx + 1,
                )
            ],
        )
        con.commit()
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
