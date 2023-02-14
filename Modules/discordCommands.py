from discord.ext import commands
from discord.ext.commands import has_permissions
import os.path

bot = commands.Bot(command_prefix='!')  # command prefix, ADD tie into ini


@bot.event  # turning bot online
async def on_ready():
    print(f"Logged in as {bot.user}")


# EVENTS
@bot.event
async def on_member_join(member):
    print(f'{member} has joined')  # ADD capability to see in game login


@bot.event
async def on_member_remove(member):
    print(f'{member} has left')  # ADD capability to see in game logout


# COMMANDS
@bot.command()
async def commands(ctx):
    if os.path.exists('commands.txt'):
        with open("commands.txt", "r") as list:
            list = list.readlines()
            for i in list:
                i = i.strip()
                await ctx.send(i)  # prints commands
    else:
        await ctx.send("Command list not available.")


# ADMIN COMMANDS
@bot.command()  # ADD try-catch for denied access
@has_permissions(administrator=True)  # is administrator
async def close(ctx):
    await bot.close()  # ADD try-catch or find something that doesnt error
    print("bot is closed")


# start bot
bot.run('')  # ADD discord tag
