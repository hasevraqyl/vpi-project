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
    """Makes a turn"""
    Game.turn()
    await interaction.response.send_message("Ход сделан")


@client.tree.command()
@app_commands.describe(
    first_value="the name of the planet",
)
async def planet(interaction: discord.Interaction, first_value: str):
    """Info about a planet."""
    system, resources = Game.fetch_Planet(first_value)
    if system is None:
        await interaction.response.send_message("Такой планеты нету.")
    else:
        await interaction.response.send_message(
            f"Планета {first_value} находится в системе {system}. \nОбщий прирост {abs(resources[0][0])}; базовая продукция {resources[0][1]}; накопленных ресурсов {abs(resources[0][2])}."
        )


@client.tree.command()
@app_commands.describe(
    first_value="the name of the planet", second_value="number of resources"
)
async def planet_add_bp(
    interaction: discord.Interaction, first_value: str, second_value: int
):
    """Add BP to a planet."""
    flag = Game.add_BP(first_value, second_value)
    if not flag:
        await interaction.response.send_message("Такой планеты нету.")
    else:
        await interaction.response.send_message(
            f"Базовая продукция увеличена на {second_value} на планете {first_value}"
        )


client.run("MTE5MDY1MDk3MjQ3Nzg0OTY5Mg.Gu1UAB.B9iQHcbcmbfwi3wzTC87YI6xeRD9qW9XMTPxpI")
