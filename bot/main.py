import os
import discord
import asyncio
from discord.ext import commands
from background_tasks import bg_tasks


async def determine_prefix(bot, message):
    return "?"

bot = commands.Bot(
    command_prefix='?',
    case_insensitive=True
)


class initialized:
    def __init__(self):
        self.started = False

    def __call__(self):
        if not self.started:
            self.started = True
            return False
        else:
            return True


started = initialized()

extensions = [

]

if __name__ == '__main__':
    for extension in extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():    
    print(len(bot.commands))
    if not started():
        await bot.loop.create_task(bg_tasks(bot))

    print('ready')


@bot.event
async def on_command_error(ctx, error):
    if type(error) == commands.errors.CheckFailure:
        await ctx.author.send(f"You cant use `{ctx.prefix}{ctx.command}` here...")
    else:
        raise error

token = os.environ.get("DISCORD_BOT_SECRET")
bot.run(token)