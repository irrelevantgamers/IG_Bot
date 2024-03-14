import discord
from discord import app_commands
import config

intents = discord.Intents.default()
intents.members = True


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False

        async def on_ready(self):
            await self.wait_until_ready()
            if not self.synced:
                await tree.sync()
                self.synced = True
            print(f"We have logged in as {self.user}")


client = aclient()
tree = app_commands.CommandTree(client)


@tree.command(name="test", description="testing")
async def self(interaction: discord.Interaction, Name: str):
    await interaction.response.send_message(f"Hello {Name}")


client.run(config.Discord_API_KEY)
