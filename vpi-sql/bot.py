import discord
from discord import app_commands
from vpimain import Game

MY_GUILD = discord.Object(id=1012047346206519326)  # replace with your guild id


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
    await interaction.response.send_message("Turn made.")


@client.tree.command()
@app_commands.describe(
    first_value="the name of the planet",
)
async def planet(interaction: discord.Interaction, first_value: str):
    """Info about a planet."""
    system, resources = Game.fetch_Planet(first_value)
    await interaction.response.send_message(
        f"System:{system}; RO:{abs(resources[0][0])}; BP:{resources[0][1]}; RS:{resources[0][2]}"
    )


@client.tree.command()
@app_commands.describe(
    first_value="the name of the planet", second_value="number of resources"
)
async def planet_add_bp(
    interaction: discord.Interaction, first_value: str, second_value: int
):
    """Add BP to a planet."""
    Game.add_BP(first_value, second_value)
    await interaction.response.send_message(
        f"Increased the BP by {second_value} on {first_value}"
    )


client.run("MTE5MDY1MDk3MjQ3Nzg0OTY5Mg.Gu1UAB.B9iQHcbcmbfwi3wzTC87YI6xeRD9qW9XMTPxpI")
