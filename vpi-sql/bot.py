import discord
from discord import app_commands
from vpimain import Game

MY_GUILD = discord.Object(id=1157327909992804456)  # replace with your guild id


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        # A CommandTree is a special type that holds all the application command
        # state required to make it work. This is a separate class because it
        # allows all the extra state to be opt-in.
        # Whenever you want to work with application commands, your tree is used
        # to store and work with them.
        # Note: When using commands.Bot instead of discord.Client, the bot will
        # maintain its own tree instead.
        self.tree = app_commands.CommandTree(self)

    # In this basic example, we just synchronize the app commands to one guild.
    # Instead of specifying a guild to every command, we copy over our global commands instead.
    # By doing so, we don't have to wait up to an hour until they are shown to the end-user.
    async def setup_hook(self):
        # This copies the global commands over to your guild.
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)


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


@client.tree.command()
async def restart(interaction: discord.Interaction):
    """Перезапускает игру. ВНИМАНИЕ! ВЫ ТОЧНО УВЕРЕНЫ?"""
    Game.rollback()
    await interaction.response.send_message(
        "Игра перезапущена и откачена к начальному состоянию."
    )


@client.tree.command()
@app_commands.describe(
    first_value="название планеты",
)
async def planet(interaction: discord.Interaction, first_value: str):
    """Информация о планете."""
    system, resources, status = Game.fetch_Planet(first_value)
    if status.name == "no_elem":
        await interaction.response.send_message("Такой планеты нету.")
    elif status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    else:
        await interaction.response.send_message(
            f"Планета {first_value} находится в системе {system}. \nОбщий прирост {abs(resources[0])}; базовая продукция {resources[1]}; накопленных ресурсов {abs(resources[2])}."
        )


@client.tree.command()
@app_commands.describe(
    first_value="название системы",
)
async def system(interaction: discord.Interaction, first_value: str):
    """Информация о системе."""
    polity, planets, status = Game.fetch_System(first_value)
    if status.name == "no_elem":
        await interaction.response.send_message("Такой системы нету.")
    elif status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    else:
        await interaction.response.send_message(
            f"Система {first_value} - часть империи {polity}. \nВ системе находятся следующие планеты: {planets}"
        )


@client.tree.command()
@app_commands.describe(
    first_value="название империи",
)
async def polity(interaction: discord.Interaction, first_value: str):
    """Информация об империи."""
    creds, systems, status = Game.fetch_Polity(first_value)
    if status.name == "no_elem":
        await interaction.response.send_message("Такой империи нету.")
    elif status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    else:
        await interaction.response.send_message(
            f"Империя {first_value} имеет баланс в {creds} кредитов. \nВ состав империи входят следующие планеты: {systems}"
        )


@client.tree.command()
@app_commands.describe(
    first_value="название планеты", second_value="количество добавляемой продукции"
)
async def planet_add_bp(
    interaction: discord.Interaction, first_value: str, second_value: int
):
    """Добавляем продукцию."""
    status = Game.add_BP(first_value, second_value)
    if status.name == "no_elem":
        await interaction.response.send_message("Такой планеты нету.")
    elif status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    else:
        await interaction.response.send_message(
            f"Базовая продукция увеличена на {second_value} на планете {first_value}"
        )


@client.tree.command()
@app_commands.describe(
    first_value="название cистемы", second_value="название новой правящей империи"
)
async def transfer(
    interaction: discord.Interaction, first_value: str, second_value: str
):
    """Передаем систему от одной империи к другой."""
    oldsys, status = Game.transfer_System(first_value, second_value)
    if status.name == "no_elem":
        await interaction.response.send_message(
            "Проверьте правильность параметров; системы либо империи не существует."
        )
    elif status.name == "no_table":
        await interaction.response.send_message("Ошибка. Перезапустите игру.")
    if status.name == "invalid_elem":
        await interaction.response.send_message(
            f"Система {first_value} уже находится под контролем империи {second_value}."
        )
    else:
        await interaction.response.send_message(
            f"Система {first_value} передана от империи {oldsys} империи {second_value}."
        )


client.run("MTE5MDY1MDk3MjQ3Nzg0OTY5Mg.Gu1UAB.B9iQHcbcmbfwi3wzTC87YI6xeRD9qW9XMTPxpI")
