import discord
import tomllib
from discord import app_commands
from vpimain import Game

with open("config.toml", mode="rb") as fp:
    info = tomllib.load(fp)

MY_GUILD = discord.Object(id=info.get("guild"))
auth_user_ids = info.get("auth_users")


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


class Message(object):
    def __init__(self):
        self._string = "Ты тварь дрожащая и права не имеешь"

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
    status = Game.turn()
    if status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    else:
        await interaction.response.send_message("Ход сделан.")


"""@client.tree.command()
async def смерть(interaction: discord.Interaction):
    Game.debug_pop()
    await interaction.response.send_message("Тучи сгущаются.")"""


@client.tree.command()
async def restart(interaction: discord.Interaction):
    message = Message()
    if interaction.user.id in auth_user_ids:
        """Перезапускает игру. ВНИМАНИЕ! ВЫ ТОЧНО УВЕРЕНЫ?"""
        Game.rollback()
        message.set_string("Игра перезапущена и откачена к начальному состоянию.")
    await interaction.response.send_message(message.string)


@client.tree.command()
@app_commands.describe(
    first_value="название планеты",
)
async def planet(interaction: discord.Interaction, first_value: str):
    """Информация о планете."""
    message = Message()
    system, resources, status = Game.fetch_Planet(first_value)
    if status.name == "no_elem":
        message.set_string("Такой планеты нет.")
    elif status.name == "no_table":
        message.set_string("Ошибка. Перезапустите игру.")
    else:
        message.set_string(
            f"""Планета {first_value} находится в системе {system}.
            \n Общий прирост {abs(resources[0])}; базовая продукция {resources[1]}; гражданская продукция {resources[2]}; военная продукция {resources[3]}; накопленных ресурсов {round(abs(resources[4]), 2)}.
            \n Население {round(resources[5], 2)}. Коэффициент занятости tbd."""
        )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название системы",
)
async def system(interaction: discord.Interaction, first_value: str):
    """Информация о системе."""
    message = Message()
    polity, planets, st, status = Game.fetch_System(first_value)
    if status.name == "no_elem":
        message.set_string("Такой системы нет.")
    elif status.name == "no_table":
        message.set_string("Ошибка. Перезапустите игру.")
    else:
        message.set_string(
            f"Система {first_value} - часть империи {polity}. \nВ системе находятся следующие планеты: {planets} {st}"
        )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название планеты",
)
async def buildings(interaction: discord.Interaction, first_value: str):
    """Информация о постройках на планете."""
    message = Message()
    builds, status = Game.planet_Buildings(first_value)
    if status.name == "no_elem":
        message.set_string("Такой системы нет.")
    elif status.name == "no_table":
        message.set_string("Ошибка. Перезапустите игру.")
    else:
        string = ""
        for building in builds:
            if building[1] != 0:
                string += (
                    f"\n {building[0]}. До окончания постройки {building[1]} ходов."
                )
            else:
                string += f"\n {building[0]}"
        message.set_string(
            f"На планете {first_value} находятся следующие постройки: {string}"
        )
    await interaction.response.send_message(message.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название планеты",
)
async def demographics(interaction: discord.Interaction, first_value: str):
    """Информация о населении планеты."""
    message = Message()
    bf, stl, pln, status = Game.planet_demos(first_value)
    if status.name == "no_elem":
        message.set_string("Такой планеты нет.")
    elif status.name == "no_table":
        message.set_string("Ошибка. Перезапустите игру.")
    elif status.name == "invalid_elem":
        message.set_string("Нет данных по населению прошлых лет.")
    else:
        if bf == []:
            message.set_string(
                f"""Текущее население на планете {first_value} - {round(pln[5], 2)}.
        За последний год население изменилось на {round((1-(stl[5]/pln[5])), 2)*100}% c {round(stl[5], 2)}."""
            )
        else:
            message.set_string(
                f"""Текущее население на планете {first_value} - {round(pln[5], 2)}.
        За последний год население изменилось на {round((1-(stl[5]/pln[5]))*100, 2)}% c {round(stl[5], 2)}.
        За последние пять лет население изменилось на {round((1-(bf[5]/pln[5]))*100, 2)}% с {round(bf[5], 2)}."""
            )
    await interaction.response.send_message(message.get_string)


@client.tree.command()
@app_commands.describe(
    first_value="название планеты",
)
async def finances(interaction: discord.Interaction, first_value: str):
    """Информация о финансах империи."""
    message = Message()
    bf, stl, pln, status = Game.polity_finances(first_value)
    if status.name == "no_elem":
        message.set_string("Такой империи нет.")
    elif status.name == "no_table":
        message.set_string("Ошибка. Перезапустите игру.")
    elif status.name == "invalid_elem":
        message.set_string("Нет данных по бюджету прошлых лет.")
    else:
        if bf == -100000.0:
            message.set_string(
                f"""В настоящий момент баланс империи {first_value} - {round(pln, 2)}. За последний год баланс изменился на {round(pln-stl, 2)} c {round(stl, 2)}."""
            )
        else:
            message.set_string(
                f"""В настоящий момент баланс империи {first_value} - {round(pln, 2)}. За последний год баланс изменился на {round(pln-stl, 2)} c {round(stl, 2)}.
        За последние пять лет баланс изменился на {round(pln-bf, 2)} с {round(bf, 2)}."""
            )
    await interaction.response.send_message(message.get_string())


"the following command has been deprecated"
"""
@client.tree.command()
@app_commands.describe(
    first_value="название планеты",
)
async def caqlculate_ql(interaction: discord.Interaction, first_value: str):
    "Информация об уровне жизни на планете."
    builds, status = Game.calculate_ql(first_value)
    if status.name == "no_elem":
        await interaction.response.send_message(
            "Такой планеты нету либо там вообще жить негде."
        )
    elif status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    else:
        await interaction.response.send_message(
            f"На планете {first_value} уровень жизни равен {builds}."
        )
        """


@client.tree.command()
@app_commands.describe(
    first_value="название империи",
)
async def polity(interaction: discord.Interaction, first_value: str):
    """Информация об империи."""
    m = Message()
    creds, systems, status = Game.fetch_Polity(first_value)
    if status.name == "no_elem":
        m.set_string("Такой империи нет.")
    elif status.name == "no_table":
        m.set_string("Ошибка. Перезапустите игру.")
    else:
        m.set_string(
            f"Империя {first_value} имеет баланс в {creds} кредитов. \nВ состав империи входят следующие системы: {systems}"
        )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название планеты", second_value="количество добавляемой продукции"
)
async def planet_add_bp(
    interaction: discord.Interaction, first_value: str, second_value: int
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Добавляем продукцию."""
        status = Game.add_BP(first_value, second_value)
        if status.name == "no_elem":
            m.set_string("Такой планеты нет.")
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string(
                f"Базовая продукция увеличена на {second_value} на планете {first_value}."
            )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(first_value="название системы", second_value="название планеты")
async def create_planet(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Создаем планету."""
        status = Game.create_planet(first_value, second_value)
        if status.name == "redundant_elem":
            m.set_string(
                "Такая планета или система уже существует в составе какой-то империи."
            )
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string(
                f"Создана планета {second_value} в составе системы {first_value}."
            )

    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(first_value="название политии", second_value="название системы")
async def claim_system(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Передаем систему политии."""
        status = Game.claim_system(first_value, second_value)
        if status.name == "no_elem":
            m.set_string("Такой системы или политии нет.")
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string(
                f"Система {second_value} передана политии {first_value} вместе с планетами."
            )
    await interaction.response.send_message(m.set_string())


@client.tree.command()
@app_commands.describe(first_value="название планеты", second_value="название здания")
async def planet_build(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Начинаем строительство на планете."""
        status = Game.build_Building(first_value, second_value)
        if status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        elif status.name == "no_elem":
            m.set_string("Такой планеты нету.")
        elif status.name == "invalid_elem":
            m.set_string("Такого здания не бывает.")
        elif status.name == "redundant_elem":
            m.set_string("Достигнут лимит зданий данного типа.")
        else:
            m.set_string(
                f"Постройка здания {second_value} успешно начата на планете {first_value}."
            )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название системы",
)
async def system_build(interaction: discord.Interaction, first_value: str):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Построить в системе станцию."""
        status = Game.build_Station(first_value)
        if status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        elif status.name == "no_elem":
            m.set_string("Такой системы нету.")
        elif status.name == "redundant_elem":
            m.set_string("В системе уже есть станция.")
        else:
            m.set_string(f"Пoстройка станции в системе {first_value} успешно начата.")
    else:
        await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название cистемы", second_value="название новой правящей империи"
)
async def transfer(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Передаем систему от одной империи к другой."""
        oldsys, status = Game.transfer_System(first_value, second_value)
        if status.name == "no_elem":
            m.set_string(
                "Проверьте правильность параметров; системы либо империи не существует."
            )
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        if status.name == "invalid_elem":
            m.set_string(
                f"Система {first_value} уже находится под контролем империи {second_value}."
            )
        else:
            m.set_string(
                f"Система {first_value} передана от империи {oldsys} империи {second_value}."
            )
    await interaction.response.send_message("Ты тварь дрожащая и права не имеешь.")


@client.tree.command()
@app_commands.describe(
    first_value="название политии", second_value="название технологии"
)
async def research_tech(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Начинаем исследование технологии."""
        cures, status = Game.research_tech(first_value, second_value)
        if status.name == "no_elem":
            m.set_string("Проверьте правильность параметров; империи не существует.")
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        if status.name == "invalid_elem":
            m.set_string("Ошибка. Технологии не существует.")
        if status.name == "redundant_elem":
            m.set_string("Технология уже исследована или исследуется.")
        if status.name == "unknown":
            m.set_string("э")
        else:
            if cures == "":
                m.set_string(f"Начато исследование технологии {second_value}")
            else:
                m.set_string(
                    f"Начато исследование технологии {second_value}. Прекращено исследование {cures}."
                )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название первой империи", second_value="название второй империи"
)
async def shengen(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Передаем систему от одной империи к другой."""
        status = Game.agree(first_value, second_value)
        if status.name == "no_elem":
            m.set_string("Проверьте правильность параметров; империи не существует.")
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        else:
            m.set_string(
                f"Заключено миграционное соглашение между империями {first_value} и {second_value}."
            )
    await interaction.response.send_message(m.get_string())


@client.tree.command()
@app_commands.describe(
    first_value="название первой планеты", second_value="название второй планеты"
)
async def deport(interaction: discord.Interaction, first_value: str, second_value: str):
    m = Message()
    if interaction.user.id in auth_user_ids:
        """Начинает депортацию населения с первой на вторую планеты."""
        status = Game.deport(first_value, second_value)
        if status.name == "no_elem":
            m.set_string(
                "Проверьте правильность параметров; одной из планет не существует."
            )
        elif status.name == "no_table":
            m.set_string("Ошибка. Перезапустите игру.")
        elif status.name == "redundant_elem":
            m.set_string(
                "Перемещение масс население между этими планетами уже имеет место."
            )
        elif status.name == "invalid_elem":
            m.set_string("Планеты не входят в состав одной империи.")
        else:
            m.set_string(
                f"Начата депортация населения с планеты {first_value} на планету {second_value}."
            )
    await interaction.response.send_message("Ты тварь дрожащая и права не имеешь.")


client.run(info.get("token"))
