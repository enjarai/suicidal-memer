import re
import json
import asyncio
import discord
from collections import abc
from datetime import timedelta, datetime
from database import Database
from itemindex import ItemIndex

db = Database("userdata.db")
index = ItemIndex("main")

def update(old, new, output=True):

    for k, v in new.items():
        if isinstance(v, abc.Mapping):
            old[k] = update(old.get(k, {}), v, False)
        else:
            old[k] = v

    return old


class LazyChannel:
    def __init__(self, channel_id):
        self.id = channel_id


class LazyGuild:
    def __init__(self, guild_id):
        self.id = int(guild_id)


class LazyAuthor:
    id = -1
    guild = None
    guild_permissions = discord.Permissions(0)
    roles = ['none']


class LazyCtx:
    def __init__(self, command, guild_id, **info):
        self.command = command
        self.guild = LazyGuild(guild_id)
        self.author = LazyAuthor()

        if 'role' in info:
            self.author.roles = [info['role']]
            self.author.guild_permissions = info['role'].permissions

        else:
            self.author.roles = []
        if 'channel_id' in info:
            self.channel = LazyChannel(info['channel_id'])
        else:
            self.channel = None


def execute(_code, loc):
    '''
    Executes code asynchronously,0 credits to mat, https://matdoes.d0ev
    '''
    _code = _code.replace('\n', '\n ')
    globs = globals()
    globs.update(loc)
    exec(
        'async def __ex():\n ' + _code,
        globs
    )
    return globs['__ex']()


async def check_allowed(ctx):
    pass


def index_args(args):
    indexed = [[]]

    for arg in args:
        if not arg.startswith('-'):
            indexed[-1].append(arg)
        else:
            indexed.append([arg])
    return indexed


class InvalidDate(BaseException):
    pass


def find_date(string):  # Credits to @mat1 for this
    times = {
        'months': timedelta(days=30),
        'month': timedelta(days=30),
        'mo': timedelta(days=30),

        'weeks': timedelta(weeks=1),
        'week': timedelta(weeks=1),
        'w': timedelta(weeks=1),

        'days': timedelta(days=1),
        'day': timedelta(days=1),
        'd': timedelta(days=1),

        'hours': timedelta(hours=1),
        'hour': timedelta(hours=1),
        'h': timedelta(hours=1),

        'minutes': timedelta(minutes=1),
        'minute': timedelta(minutes=1),
        'm': timedelta(minutes=1),

        'seconds': timedelta(seconds=1),
        'second': timedelta(seconds=1),
        's': timedelta(seconds=1),
    }
    leftover_string = string
    total_time = timedelta()
    while leftover_string:
        found_match = None
        found_time = None
        for t in times:
            matched = re.match(r'^(\d+) ?' + t, leftover_string)
            if matched is not None:
                found_match = matched
                found_time = times[t]
                break
        if found_match is None:
            raise InvalidDate(f'Invalid date "{string}"')
        amount = matched.group(1)
        added_time = found_time * int(amount)
        total_time += added_time

        string_end = found_match.span()[1]

        leftover_string = leftover_string[string_end:]
        leftover_string = leftover_string.strip()
    return total_time
