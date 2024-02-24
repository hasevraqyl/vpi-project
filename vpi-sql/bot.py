import discord
import tomllib
from discord import app_commands
from vpimain import Game

with open("config.toml", mode="rb") as fp:
    info = tomllib.load(fp)

MY_GUILD = discord.Object(id=info.get("guild"))


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


class Message(object):
    def __init__(self, interaction):
        if interaction.user.id not in info.get("auth_users"):
            self._string = "Ты тварь дрожащая и права не имеешь."
            self._auth = False
        else:
            self._auth = True

    def auth(self):
        return self._auth

    def fill_string(self, status, no_elem):
        if status == "no_table":
            self._string = "Ошибка. Перезапустите игру."
            return False
        elif status == "no_elem":
            self._string = f"Такой {no_elem} не существует."
            return False
        elif status == "unknown":
            self._string = "Неизвестная ошибка."
            return False
        else:
            return True

    def set_string(self, val):
        self._string = val

    def get_string(self):
        return self._string


intents = discord.Intents.default()
client = MyClient(intents=intents)


@client.event
async def on_ready():
    print(f"Logged in as {client.user} (ID: {client.user.id})")
    print("------")


@client.tree.command()
async def turn(interaction: discord.Interaction):
    """Совершает ход"""
    m = Message(interaction)
    if m.auth():
        status = Game.turn()
        if status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string("Ход сделан.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
async def polities(interaction: discord.Interaction):
    """Выводит список политий"""
    m = Message(interaction)
    if m.auth():
        list, status = Game.polity_list()
        if status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string(f"Существуют следующие политии: {list}")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
async def unclaimed_systems(interaction: discord.Interaction):
    """Выводит список систем, никому не принадлежащих"""
    m = Message(interaction)
    if m.auth():
        list, status = Game.unclaimed_systems()
        if status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string(f"Существуют следующие ничейные системы: {list}")
    await interaction.response.send_message(m.get_string())


"""@client.tree.command()
async def смерть(interaction: discord.Interaction):
    Game.debug_pop()
    await interaction.response.send_message("Тучи сгущаются.")"""


@client.tree.command()
async def restart(interaction: discord.Interaction):
    """Перезапускает игру. ВНИМАНИЕ! ВЫ ТОЧНО УВЕРЕНЫ?"""
    m = Message(interaction)
    if m.auth():
        Game.rollback()
        m.set_string("Игра перезапущена и откачена к начальному состоянию.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    name="название планеты",
)
async def planet(interaction: discord.Interaction, name: str):
    """Информация о планете."""
    message = Message(interaction)
    if message.auth():
        system, resources, status = Game.fetch_Planet(name)
        if message.fill_string(status, "планеты"):
            message.set_string(
                f"""Планета {name} находится в системе {system}.
                \n Общий прирост {abs(resources[0])}; базовая продукция {resources[1]}; гражданская продукция {resources[2]}; военная продукция {resources[3]}; накопленных ресурсов {round(abs(resources[4]), 2)}.
                \n Население {round(resources[5], 2)}. Коэффициент занятости tbd."""
            )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    polity="название политии",
)
async def station_list(interaction: discord.Interaction, polity: str):
    """Информация о планете."""
    message = Message(interaction)
    if message.auth():
        list, ilist, status = Game.station_list(polity)
        if message.fill_string(status, "империи"):
            message.set_string(
                f"В империи {polity} станции есть в следующих системах: {list}\nСтроятся станции в следующих системах: {ilist}"
            )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название системы",
)
async def system(interaction: discord.Interaction, name: str):
    """Информация о системе."""
    message = Message(interaction)
    if message.auth():
        polity, planets, st, status = Game.fetch_System(name)
        if message.fill_string(status, "системы"):
            if st is None:
                sst = ""
            elif st == 0:
                sst = "В системе есть станция."
            else:
                sst = f"В системе есть строящаяся станция. До завершения {st} ходов."
            message.set_string(
                f"Система {name} - часть империи {polity}. \nВ системе находятся следующие планеты: {planets} {sst}"
            )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название незаселенной системы",
)
async def unclaimed(interaction: discord.Interaction, name: str):
    """Информация о незаселенной системе."""
    message = Message(interaction)
    if message.auth():
        planets, status = Game.fetch_Unclaimed(name)
        if message.fill_string(status, "системы"):
            message.set_string(
                f"Система {name} незаселена. \n В системе находятся следующие планеты: {planets}."
            )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название новой системы",
)
async def new_system(interaction: discord.Interaction, name: str):
    """Создание новой незаселенной системы."""
    message = Message(interaction)
    if message.auth():
        status = Game.generate_system(name)
        if message.fill_string(status, ""):
            message.set_string("Система успешно сгенерированна.")
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название планеты",
)
async def buildings(interaction: discord.Interaction, name: str):
    """Информация о постройках на планете."""
    message = Message(interaction)
    if message.auth():
        builds, status = Game.planet_Buildings(name)
        if message.fill_string(status, "планеты"):
            string = ""
            for building in builds:
                if building[1] != 0:
                    string += (
                        f"\n {building[0]}. До окончания постройки {building[1]} ходов."
                    )
                else:
                    string += f"\n {building[0]}"
            message.set_string(
                f"На планете {name} находятся следующие постройки: {string}"
            )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название планеты",
)
async def demographics(interaction: discord.Interaction, name: str):
    """Информация о населении планеты."""
    message = Message(interaction)
    if message.auth():
        bf, stl, pln, status = Game.planet_demos(name)
        if message.fill_string(status, "планеты"):
            if status.name == "invalid_elem":
                message.set_string("Нет данных по населению прошлых лет.")
            else:
                if bf == []:
                    message.set_string(
                        f"""Текущее население на планете {name} - {round(pln[5], 2)}.
                За последний год население изменилось на {round((1-(stl[5]/pln[5])), 2)*100}% c {round(stl[5], 2)}."""
                    )
                else:
                    message.set_string(
                        f"""Текущее население на планете {name} - {round(pln[5], 2)}.
                За последний год население изменилось на {round((1-(stl[5]/pln[5]))*100, 2)}% c {round(stl[5], 2)}.
                За последние пять лет население изменилось на {round((1-(bf[5]/pln[5]))*100, 2)}% с {round(bf[5], 2)}."""
                    )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название планеты",
)
async def finances(interaction: discord.Interaction, name: str):
    """Информация о финансах империи."""
    message = Message(interaction)
    if message.auth():
        bf, stl, pln, status = Game.polity_finances(name)
        if message.fill_string(status, "империи"):
            if status.name == "invalid_elem":
                message.set_string("Нет данных по бюджету прошлых лет.")
            else:
                if bf == -100000.0:
                    message.set_string(
                        f"""В настоящий момент баланс империи {name} - {round(pln, 2)}. За последний год баланс изменился на {round(pln-stl, 2)} c {round(stl, 2)}."""
                    )
                else:
                    message.set_string(
                        f"""В настоящий момент баланс империи {name} - {round(pln, 2)}. За последний год баланс изменился на {round(pln-stl, 2)} c {round(stl, 2)}.
                За последние пять лет баланс изменился на {round(pln-bf, 2)} с {round(bf, 2)}."""
                    )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    name="название империи",
)
async def polity(interaction: discord.Interaction, name: str):
    """Информация об империи."""
    m = Message(interaction)
    if m.auth():
        creds, systems, status = Game.fetch_Polity(name)
        if m.fill_string(status, "империи"):
            m.set_string(
                f"Империя {name} имеет баланс в {creds} кредитов. \nВ состав империи входят следующие системы: {systems}"
            )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    name="название планеты", amount="количество добавляемой продукции"
)
async def planet_add_bp(interaction: discord.Interaction, name: str, amount: int):
    """Добавляем продукцию."""
    m = Message(interaction)
    if m.auth():
        status = Game.add_BP(name, amount)
        if m.fill_string(status, "планеты"):
            m.set_string(f"Базовая продукция увеличена на {amount} на планете {name}.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(system="название системы", planet="название планеты")
async def create_planet(interaction: discord.Interaction, system: str, planet: str):
    """Создаем планету."""
    m = Message(interaction)
    if m.auth():
        status = Game.create_planet(system, planet)
        if m.fill_string(status, ""):
            if status.name == "redundant_elem":
                m.set_string(
                    "Такая планета или система уже существует в составе какой-то империи."
                )
            else:
                m.set_string(f"Создана планета {planet} в составе системы {system}.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(polity="название политии", system="название системы")
async def claim_system(interaction: discord.Interaction, polity: str, system: str):
    """Передаем систему политии."""
    m = Message(interaction)
    if m.auth():
        status = Game.claim_system(polity, system)
        if m.fill_string(status, "системы или политии"):
            m.set_string(
                f"Система {system} передана политии {polity} вместе с планетами."
            )
    await interaction.response.send_message(m.set_string())


@client.tree.command()
@app_commands.describe(name="название планеты", building="название здания")
async def planet_build(interaction: discord.Interaction, name: str, building: str):
    """Начинаем строительство на планете."""
    m = Message(interaction)
    if m.auth():
        status = Game.build_Building(name, building)
        if m.fill_string(status, "планеты"):
            if status.name == "invalid_elem":
                m.set_string("Такого здания не бывает.")
            elif status.name == "redundant_elem":
                m.set_string("Достигнут лимит зданий данного типа.")
            else:
                m.set_string(
                    f"Постройка здания {building} успешно начата на планете {name}."
                )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    name="название системы",
)
async def system_build(interaction: discord.Interaction, name: str):
    """Построить в системе станцию."""
    m = Message(interaction)
    if m.auth():
        status = Game.build_Station(name)
        if m.fill_string(status, "системы"):
            if status.name == "redundant_elem":
                m.set_string("В системе уже есть станция.")
            else:
                m.set_string(f"Пoстройка станции в системе {name} успешно начата.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    name="название системы",
)
async def ship_build(interaction: discord.Interaction, name: str):
    """Построить в системе корабль."""
    m = Message(interaction)
    if m.auth():
        status = Game.build_Ship(name)
        if m.fill_string(status, "верфи"):
            if status.name == "redundant_elem":
                m.set_string("В системе уже строится корабль.")
            else:
                m.set_string(f"Пoстройка корябля в системе {name} успешно начата.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(name="название системы", building="название здания")
async def station_build(interaction: discord.Interaction, name: str, building: str):
    """Начинаем строительство на станции."""
    m = Message(interaction)
    if m.auth():
        status = Game.improve_Station(name, building)
        if m.fill_string(status, "системы либо станции в системе"):
            if status.name == "invalid_elem":
                m.set_string("Такого здания не бывает.")
            elif status.name == "redundant_elem":
                m.set_string("Достигнут лимит зданий данного типа.")
            else:
                m.set_string(
                    f"Постройка здания {building} успешно начата на станции в системе {name}."
                )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    polity="название политиии",
    module="название модуля",
    template="название темплейта",
)
async def module_build(
    interaction: discord.Interaction,
    polity: str,
    module: str,
    template: str,
):
    """Добавляем модуль в темплейт."""
    m = Message(interaction)
    if m.auth():
        status = Game.build_module(polity, module, template)
        if m.fill_string(status, "темплейта"):
            if status.name == "invalid_elem":
                m.set_string("Такого модуля не бывает.")
            elif status.name == "redundant_elem":
                m.set_string("Достигнут лимит лимита.")
            else:
                m.set_string(
                    f"Модуль {module} успешно установлен в темплейт {template}."
                )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    polity="название политиии",
    name="название темплейта",
    cost="стоимость темплейта",
)
async def template_build(
    interaction: discord.Interaction,
    polity: str,
    name: str,
    cost: float,
):
    """Создаем темплейт."""
    m = Message(interaction)
    if m.auth():
        status = Game.build_Template(polity, name, cost)
        if m.fill_string(status, "политии"):
            if status.name == "redundant_elem":
                m.set_string("Такой темплейт уже есть.")
            else:
                m.set_string(f"Темплейт {name} успешно создан, стоимость - {cost}.")
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    system="название cистемы", polity="название новой правящей империи"
)
async def transfer(interaction: discord.Interaction, system: str, polity: str):
    """Передаем систему от одной империи к другой."""
    m = Message(interaction)
    if m.auth():
        oldsys, status = Game.transfer_System(system, polity)
        if m.fill_string(status, "системы либо империи"):
            if status.name == "invalid_elem":
                m.set_string(
                    f"Система {system} уже находится под контролем империи {polity}."
                )
            else:
                m.set_string(
                    f"Система {system} передана от империи {oldsys} империи {polity}."
                )
    await interaction.response.send_message("Ты тварь дрожащая и права не имеешь.")


@client.tree.command()
@app_commands.describe(polity="название политии", tech="название технологии")
async def research_tech(interaction: discord.Interaction, polity: str, tech: str):
    """Начинаем исследование технологии."""
    m = Message(interaction)
    if m.auth():
        cures, status = Game.research_tech(polity, tech)
        if m.fill_string(status, "империи"):
            if status.name == "invalid_elem":
                m.set_string("Ошибка. Технологии не существует.")
            if status.name == "redundant_elem":
                m.set_string("Технология уже исследована или исследуется.")
            else:
                if cures == "":
                    m.set_string(f"Начато исследование технологии {tech}")
                else:
                    m.set_string(
                        f"Начато исследование технологии {tech}. Прекращено исследование {cures}."
                    )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_polity="название первой империи", second_polity="название второй империи"
)
async def shengen(
    interaction: discord.Interaction, first_polity: str, second_polity: str
):
    """Передаем систему от одной империи к другой."""
    m = Message(interaction)
    if m.auth():
        status = Game.agree(first_polity, second_polity)
        if m.fill_string(status, "империи"):
            m.set_string(
                f"Заключено миграционное соглашение между империями {first_polity} и {second_polity}."
            )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_planet="название первой планеты", second_planet="название второй планеты"
)
async def deport(
    interaction: discord.Interaction, first_planet: str, second_planet: str
):
    """Начинает депортацию населения с первой на вторую планеты."""
    m = Message(interaction)
    if m.auth():
        status = Game.deport(first_planet, second_planet)
        if m.fill_string(status, "планеты"):
            if status.name == "redundant_elem":
                m.set_string(
                    "Перемещение масс население между этими планетами уже имеет место."
                )
            elif status.name == "invalid_elem":
                m.set_string("Планеты не входят в состав одной империи.")
            else:
                m.set_string(
                    f"Начата депортация населения с планеты {first_planet} на планету {second_planet}."
                )
    await interaction.response.send_message("Ты тварь дрожащая и права не имеешь.")


client.run(info.get("token"))
