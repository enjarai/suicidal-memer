#!/usr/bin/env python3
import discord
from discord.ext import commands
import json
import random
import asyncio
import subprocess
import operator
import configparser
import glob
import emoji
import datetime
import sys
import traceback
client = commands.Bot(command_prefix=("plzz ", "Plzz ", "plz ", "Plz "))
client.remove_command("help")

# custom imports
from itemindex import Item, ItemIndex
from database import Database

lastid = {}

config = configparser.ConfigParser()
config.read_file(open("config.conf", "r"))
token = config.get("config", "token")
channelid = config.get("config", "triviachannel")
triviaminwait = int(config.get("config", "triviaminwait"))
triviamaxwait = int(config.get("config", "triviamaxwait"))
index = ItemIndex("main")

enabletrubot = config.getboolean('trubot', 'enabled') 
trutoken = config.get("trubot", "token")
truversion = config.get("trubot", "version")

if enabletrubot:
    trubot = commands.Bot(command_prefix="trubot ")
    trubot.remove_command("help")

#read "database"
db = Database("userdata.db")

#read counters
with open("counters.json", "r") as f:
    counters = json.load(f)

qdir = glob.glob("./questions/*.json")
questions = []
for i in qdir:
    with open(i, "r") as f:
        q = json.load(f)
    questions.append(q)

trivia = {
    "next": True,
    "channel": None
}
triviamultiplier = 10
levelcost = 60

effectemoji = {
    "dice": "<:dice:632295947552030741>",
    "uno": "<:unoshield:720992427216863302>",
    "vault": "<:vault:699266653791322172>"
}

#=================================== item defintions ===================================#

index.add(
    name="Points",
    emoji="<:coin:632592319245451286>",
    lootboxmax=400,
    lootboxweight=2000,
    genaliases=False
)


async def item_lootbox(ctx):
    """
    This is a loot box, in case you hadn't guessed.

    Here are some drop rates i guess:
    """
    embed = discord.Embed(title="Loot Box opened!", description="You got:", colour=discord.Colour(0x70a231))
    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    for i in range(3):
        weights = []
        for item in index.items:
            weights.append(item.lootboxweight)
        addthis = random.choices(index.items, weights)[0]
        amount = random.randint(1, addthis.lootboxmax)
        if addthis.id == 0:
            embed.add_field(name="<:coin:632592319245451286>", value=f"{amount} Points", inline=True)
            db.update_bal(ctx.author.id, amount)
        else:
            embed.add_field(name=addthis.emoji, value=f"{amount}x {addthis.name}", inline=True)
            db.give_item(ctx.author.id, addthis.id, amount)
    await ctx.send(embed=embed)
    return True

index.add(
    use=item_lootbox,
    name="Loot Box",
    emoji="<:lootbox:632286669592199217>",
    aliases=[],
    description="Some say it's gambling, so imma add it while it's legal...",
    buy=500,
    sell=250
)


async def item_dice(ctx, amount: int):
    """
    Using this instead of gambling increases your chance of winning to 66%.
    (Don't use this at a real casino, cus i think thats illegal)

    *\* it has been reworked! wow*
    """
    odds = [66, 34]

    return await int_gamble(ctx, amount, odds)

index.add(
    use=item_dice,
    name="Loaded Dice",
    emoji="<:dice:632295947552030741>",
    sell=100,
    useargs="i"
)


async def item_spambot(ctx, member):
    """
    You all know that feeling when your friends are online,
    but they never respond to your messages.
    This item is the solution to that problem!

    Using this item on another user will spam the chat with their pings.
    Now available for only $19.99! *terms and conditions apply*

    *\* please dont abuse :)*
    """
    for i in range(4):
        await ctx.send(member.mention + ": get the fuck over here")
    amount = random.randint(10, 30)
    await ctx.send(ctx.author.mention + f": {member.mention} was so startled they dropped {amount} <:coin:632592319245451286>")
    db.update_bal(member.id, -amount)
    db.update_bal(ctx.author.id, amount) # add cooldown?
    return True

index.add(
    use=item_spambot,
    name="Spambot",
    emoji="<:spambot:632466831063646221>",
    aliases=["bot", "spam"],
    description="Spams the crap out of your target",
    lootboxmax=5,
    lootboxweight=2000,
    buy=100,
    sell=15,
    useargs="m"
)


async def item_mask(ctx, member):
    """
    You filthy thief!
    Stealing up to 300 points from your friends using this item is not nice.
    I sure do hope they have vaults active to stop you...

    *\* Elysium Corp is not responsible for any bans as the result of robbing admins*
    """
    memscore = db.get_bal(member.id)
    if memscore >= 300:
        amount = random.randint(40, 300)
    elif memscore < 50:
        amount = 0
    else:
        amount = random.randint(40, memscore)
    if amount:
        memeff = db.get_eff(member.id)
        if "uno" in memeff:
            amount = amount * 2
            db.update_bal(member.id, amount)
            db.update_bal(ctx.author.id, -amount)
            await ctx.send(ctx.author.mention + f": You robbed {member.mention}, but they had an uno reverse card active! you lost `{amount}` points!")
            db.rem_eff(member.id, "uno")
        elif "vault" in memeff:
            await ctx.send(ctx.author.mention + f": You robbed {member.mention}, but they had a vault active and you lost your mask!")
            db.rem_eff(member.id, "vault")
        else:
            db.update_bal(member.id, -amount)
            db.update_bal(ctx.author.id, amount)
            db.log(member.id, "steal", ctx.author.id, amount)
            await ctx.send(ctx.author.mention + f": You robbed {member.mention}, you managed to get away with `{amount}` points!")
    else:
        await ctx.send(ctx.author.mention + f": You cant rob {member.mention}! They're way too poor, thats pathetic... *shakes head disapprovingly*")
        return False
    return True

index.add(
    use=item_mask,
    name="Robbers Mask",
    emoji="<:balaclava:632658938437042212>",
    aliases=[],
    description="Use this to steal some points from your buddies, i'm sure they won't hate you...",
    lootboxmax=1,
    lootboxweight=400,
    buy=400,
    sell=200,
    useargs="m"
)


async def item_bread(ctx):
    """
    Okay seriously thats gross, its almost like a new lifeform has evolved here!
    Wait you wanna eat this? Would you even survive that?!

    Actually eating it seems to just remove 10 points.
    But it doesn't stop you from eating it is you have no points left, that might be worth investigating...

    *\* this might get really useful later on, once i get around to adding the thing*
    """
    await ctx.send(ctx.author.mention + ": You ate the Moldy Bread, why the fuck would you do that? *backs away slowly*\nU got -10 <:coin:632592319245451286> cus thats just nasty")
    db.update_bal(ctx.author.id, -10)
    return True

index.add(
    use=item_bread,
    name="Moldy Bread",
    emoji="<:moldybread:632921575649443909>",
    aliases=[],
    description="Why would you keep this?",
    lootboxmax=1,
    lootboxweight=100,
    buy=20,
    sell=5
)


async def item_fortune(ctx):
    """
    "A fortune cookie is a crisp and sugary cookie usually made from flour, sugar, vanilla, and sesame seed oil with a piece of paper inside, a "fortune", on which is an aphorism, or a vague prophecy."
    *(from https://en.wikipedia.org/wiki/Fortune_cookie)*

    Well Wikipedia isn't wrong, but there might be more to it than that...

    *\* expect more here in the future*
    """
    await ctx.send(ctx.author.mention + f""": You cracked open the cookie, the little piece of paper inside says:\n```{subprocess.check_output(["/usr/games/fortune"]).decode("utf-8")}```""")
    if random.randint(1, 10) == 1:
        cash = random.randint(50, 300)
        await ctx.send(ctx.author.mention + f""": There were also {cash} <:coin:632592319245451286> hidden inside!""")
        db.update_bal(ctx.author.id, cash)
        # add item drops rarely, better than lootbox?
    return True

index.add(
    use=item_fortune,
    name="Fortune Cookie",
    emoji="<:fortunecookie:633286682195525653>",
    aliases=[],
    description="Tells you your fortune i guess, sometimes has something hidden inside tho",
    lootboxmax=10,
    lootboxweight=1500,
    buy=80,
    sell=5
)


async def item_nuke(ctx, member):
    """
    Pretty cool right, having a nuke in your pocket?
    Using this is more effective than just putting on a mask, just like real life!

    This is more effective at stealing points, but there's also some collateral damage.

    *\* tbh, it is not that good, thats why it's on discount :/*
    """
    memscore = db.get_bal(member.id)
    if memscore >= 500:
        amount = random.randint(0, 500)
    elif memscore < 0:
        amount = -random.randint(0, -memscore)
    elif memscore < 500:
        amount = random.randint(0, memscore)
    memeff = db.get_eff(member.id)
    if "uno" in memeff:
        amount = amount * 2
        db.update_bal(member.id, int(amount / 2))
        db.update_bal(ctx.author.id, -amount)
        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, but they had an uno reverse card active! you lost `{amount}` points, and half of them were destroyed!")
        db.rem_eff(member.id, "uno")
    elif "vault" in memeff:
        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, but they had a vault active!")
        db.rem_eff(member.id, "vault")
    else:
        db.update_bal(member.id, -amount)
        db.update_bal(ctx.author.id, int(amount / 2))
        db.log(member.id, "steal", ctx.author.id, amount)
        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, you stole `{amount}` points, but half of them were destroyed!")
    return True

index.add(
    use=item_nuke,
    name="Nuke",
    emoji="<:nuke:671718044078440448>",
    aliases=[],
    description="Steals points from pals but destroys half of 'em, **90% discount!**",
    lootboxmax=1,
    lootboxweight=200,
    buy=100,
    sell=50,
    useargs="m"
)


async def item_nuke2(ctx, member):
    """
    Fuck your friends in the ass today with the new NUKE 2: ELECTRIC BOOGALOO,
    as opposed to the old nuke this one is acually better than a mask! *wow*

    This is exactly the same as the normal nuke, but more destructive.

    *\* where the normal nuke destroyed one city, this one destroys about 5 at least*
    """
    memscore = db.get_bal(member.id)
    if memscore >= 1000:
        amount = random.randint(0, 1000)
    elif memscore < 0:
        amount = -random.randint(0, -memscore)
    elif memscore < 1000:
        amount = random.randint(int(memscore * 0.4), memscore)
    memeff = db.get_eff(member.id)
    if "uno" in memeff:
        amount = amount * 2
        db.update_bal(member.id, int(amount / 2))
        db.update_bal(ctx.author.id, -amount)
        await ctx.send(ctx.author.mention + f": You yeeted a nuke 2: electric boogaloo at {member.mention}, but they had an uno reverse card active! you lost `{amount}` points, and half of them were destroyed!")
        db.rem_eff(member.id, "uno")
    elif "vault" in memeff:
        await ctx.send(ctx.author.mention + f": You yeeted a nuke 2: electric boogaloo at {member.mention}, but they had a vault active!")
        db.rem_eff(member.id, "vault")
    else:
        db.update_bal(member.id, -amount)
        db.update_bal(ctx.author.id, int(amount / 2))
        db.log(member.id, "steal", ctx.author.id, amount)
        await ctx.send(ctx.author.mention + f": You yeeted a nuke 2: electric boogaloo at {member.mention}, you stole `{amount}` points, but half of them were destroyed!")
    return True

index.add(
    use=item_nuke2,
    name="Nuke 2: Electric Boogaloo",
    emoji="<:nuke2:698057397574303784>",
    aliases=["nuke2"],
    description="The cooler daniel, no discount here",
    lootboxmax=1,
    lootboxweight=80,
    buy=1000,
    sell=300,
    useargs="m"
)


async def item_unoshield(ctx):
    """
    Okay so we're playing uno now apparently,
    this acually seems pretty useful though.

    The reverse shield can reverse a single rob or nuke.
    After that it just disappears. like, \*poof\*, and its gone.

    *\* oh yeah, and it doubles the amount robbed. so thats nice...*
    """
    if "uno" in db.get_eff(ctx.author.id):
        await ctx.send(ctx.author.mention + f""": You already have a reverse shield active""")
        return False
    else:
        await ctx.send(ctx.author.mention + f""": Uno Reverse Shield activate! you are now protected from one rob/nuke""")
        db.give_eff(ctx.author.id, "uno")
    return True

index.add(
    use=item_unoshield,
    name="Reverse Shield",
    emoji="<:unoshield:720992427216863302>",
    aliases=["unoshield", "reverseshield", "shield"],
    description="Use this to ward off those pesky thieves once and for all",
    lootboxmax=1,
    lootboxweight=40,
    buy=1200,
    sell=800,
    genaliases=False
)


async def item_vault(ctx):
    """
    This miraculous item seems to be able to stop an entire nuke!
    It does also break from a simple robbery though...

    Use a vault to protect your points from robberies and nukes.
    After activating a vault it will protect your balance from a single attack!
    You can have 3 vaults active at once, plus a single uno card.

    *\* It's not as useful since the introduction of the lockpick...*
    """
    autheff = db.get_eff(ctx.author.id)
    if "vault" in autheff:
        if autheff["vault"] < 3:
            db.give_eff(ctx.author.id, "vault")
        else:
            await ctx.send(ctx.author.mention + f""": You already have 3 vaults active""")
            return False
    else:
        db.give_eff(ctx.author.id, "vault")
    await ctx.send(ctx.author.mention + f""": Used item""")
    return True

index.add(
    use=item_vault,
    name="Vault",
    emoji="<:vault:699266653791322172>",
    aliases=[],
    description="Protect your precious points, stops one attack each, 3 allowed active at once",
    lootboxmax=1,
    lootboxweight=400,
    buy=200,
    sell=150
)


async def item_lockpick(ctx, member):
    """
    Wasting masks and nukes on removing vaults is not very nice is it?
    
    This item can remove a single active vault from someone's balance.
    Once there are no vaults left it's pretty much useless...

    *\* okay so i might have made this a bit too common...*
    """
    if "vault" in db.get_eff(member.id):
        db.rem_eff(member.id, "vault")
        await ctx.send(ctx.author.mention + f""": You cracked one of {member.mention}'s vaults!'""")
    else:
        await ctx.send(ctx.author.mention + f""": {member.mention} has no vaults active""")
        return False
    return True

index.add(
    use=item_lockpick,
    name="Lockpick",
    emoji="<:lockpick:699275348675657788>",
    aliases=[],
    description="Removes a vault, nothing else",
    lootboxmax=2,
    lootboxweight=1000,
    buy=300,
    sell=150,
    useargs="m"
)

async def item_rulebook(ctx, member):
    """
    Wasting masks and nukes on removing ~~vaults~~ **reverse shields** is not very nice is it?
    
    This item can remove a single active ~~vault~~ **reverse shields** from someone's balance.
    Once there are no ~~vaults~~ **reverse shields** left it's pretty much useless...

    *\* okay so i might have made this a bit too uncommon...*
    """
    if "uno" in db.get_eff(member.id):
        db.rem_eff(member.id, "uno")
        await ctx.send(ctx.author.mention + f""": You annihilated {member.mention}'s reverse shield!""")
    else:
        await ctx.send(ctx.author.mention + f""": {member.mention} has no reverse shield active""")
        return False
    return True

index.add(
    use=item_rulebook,
    name="Uno Rulebook",
    emoji="<:rulebook:718503942153044081>",
    aliases=["rulebook", "rules", "unorulebook", "book", "rule"],
    description="Another counter item",
    lootboxmax=1,
    lootboxweight=20,
    buy=1400,
    sell=1000,
    useargs="m",
    genaliases=False
)


index.add(
    # use=item_rulebook,
    name="Unknown",
    # emoji="<:rulebook:718503942153044081>",
    aliases=["nuke3"],
    description="",
    # lootboxmax=1,
    # lootboxweight=20,
    buy=0,
    sell=0,
    useargs="m",
    genaliases=False
)


async def item_unocard(ctx):
    """
    This uno card seems different...
    
    If this item is used within one hour of a rob/nuke the effect can be reversed, making the attacker lose points!
    This is *not* limited to only the most recent rob/nuke.

    *\* this seemed a bit more appropriate for the uno card*
    """
    dbreturn = db.latest_log(ctx.author.id, "steal")
    try:
        affected, amount = dbreturn
    except TypeError:
        await ctx.send(ctx.author.mention + f""": You have no recent robs to reverse""")
        return False

    db.update_bal(affected, -amount * 2)
    db.update_bal(ctx.author.id, amount * 2)
    await ctx.send(ctx.author.mention + f""": You reversed {client.get_user(affected).mention}'s rob of {amount} {index.get_by_id(0).emoji}!""")

    return True

index.add(
    use=item_unocard,
    name="Uno Reverse Card",
    emoji="<:unoreverse:699194687646597130>",
    aliases=["unoreverse"],
    description="Reverse that shit!",
    lootboxmax=1,
    lootboxweight=300,
    buy=500,
    sell=250
)

#=================================== /item defintions ==================================#

print("connecting...")


def check(payload):
    return payload.channel_id == int(channelid) and not payload.user_id == client.user.id

async def getmember(ctx, args):
    if len(args) == 1:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(args[0])
        if member:
            return member
   
    member = ctx.author

    return member

async def background():
    await client.wait_until_ready()
    channel = client.get_channel(int(channelid))
    while True:
        slp = random.randint(triviaminwait, triviamaxwait)
        print("Waiting {} seconds".format(slp))
        await asyncio.sleep(slp)
        q = random.choice(questions)
        qstr = q["text"]
        for k, i in q["options"].items():
            qstr += "\n" + f"{k}: {i}"
        embed = discord.Embed(title="Minecraft Trivia Question:", description=qstr, color=0x51e443)
        embed.set_thumbnail(url="https://icons.iconarchive.com/icons/papirus-team/papirus-apps/512/minecraft-icon.png")
        embedmsg = await channel.send(embed=embed)
        for k, i in q["options"].items():
            await embedmsg.add_reaction(emoji.emojize(k, use_aliases=True))
        tries = 0
        while True:
            payload = await client.wait_for("raw_reaction_add", check=check)
            guild = client.get_guild(payload.guild_id)
            member = guild.get_member(payload.user_id)
            channel = guild.get_channel(payload.channel_id)
            rawemoji = payload.emoji
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(rawemoji, member)
            if emoji.demojize(str(rawemoji), use_aliases=True) in q["correct"]:
                points = (10 - (2 * tries)) * triviamultiplier
                embed=discord.Embed(description="🟢 {} has earned {} points!".format(member, points))
                await channel.send(embed=embed)
                db.update_bal(member.id, points)
                if random.randint(1, 10) == 1:
                    lootbox = index.get_by_id(1)
                    db.give_item(member.id, lootbox.id, 1)
                    await channel.send(f"{member.mention}: Wow, you found a {str(lootbox)}!")
                break
            else:
                if tries < 4:
                    tries += 1
                embed=discord.Embed(description="🔴 {} has answered wrongly!".format(member))
                await channel.send(embed=embed)

async def background2():
    await client.wait_until_ready()
    print("background2 active")
    while True:
        await asyncio.sleep(5)
        for counter in counters:
            timeobj = datetime.datetime.strptime(counter["time"], '%Y-%m-%dT%H:%M:%S')
            timediff = timeobj - datetime.datetime.now()
            guild = client.get_guild(counter["guild"])
            channel = guild.get_channel(counter["channel"])
            message = await channel.fetch_message(counter["message"])
            if timediff.total_seconds() >= 0:
                text = ''.join(str(timediff).split('.')[:1])
            else:
                text = "Completed!"
            await message.edit(content=text)


#WIP
async def background4():
    await client.wait_until_ready()
    print("background4 active")
    while True:
        await asyncio.sleep(5)
        if trivia["next"]:
            slp = random.randint(triviaminwait, triviamaxwait)
            print("Waiting {} seconds".format(slp))
            await asyncio.sleep(slp)

# @client.event
# async def on_command_error(ctx, exception):
#     if hasattr(ctx.command, 'on_error'):
#         return

#     print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
#     traceback.print_exception(type(exception), exception, exception.__traceback__, file=sys.stderr)

#     await ctx.send("")

# @client.event
# async def on_member_join(member):
#     db.setup_user(member.id)


@client.event
async def on_message(message):
    if not message.author.id == client.user.id:
        db.setup_user(message.author.id)
        if not str(message.channel.id) in lastid:
            lastid[str(message.channel.id)] = 0
        if not message.author.id == lastid[str(message.channel.id)]:
            lastid[str(message.channel.id)] = message.author.id
            db.update("xp", message.author.id, 1)
            if db.get("xp", message.author.id) >= levelcost:
                db.update("xp", message.author.id, -levelcost)
                db.update("level", message.author.id, 1)
                lootbox = index.get_by_id(1)
                await message.channel.send(f"""{message.author.mention}: Holy shit, you leveled up! Now level `{db.get("level", message.author.id)}`\nWow, you found a {str(lootbox)}!""")
                db.give_item(message.author.id, lootbox.id, 1)
    await client.process_commands(message)


@client.command(aliases=["bal", "money", "status"])
async def points(ctx, *args):
    """CAPITALISM BOYS"""
    member = await getmember(ctx, args)

    memeff = db.get_eff(member.id)
    vaults = []
    if "vault" in memeff:
        vaultsnum = memeff["vault"]
    else:
        vaultsnum = 0

    for i in range(vaultsnum):
        vaults.append(effectemoji["vault"])
    for i in range(3 - vaultsnum):
        vaults.append("⭕")
    if "uno" in memeff:
        vaults.append("(" + effectemoji["uno"] + ")")
    vaults = " ".join(vaults)

    embed = discord.Embed(title="Status:", description=f"{db.get_bal(member.id)} <:coin:632592319245451286>\n**Active vaults:**\n{vaults}", colour=discord.Colour(0x70a231))
    embed.set_author(name=member.name, icon_url=member.avatar_url)
    await ctx.send(embed=embed)


@client.command(aliases=["payme", "daily"])
async def salary(ctx):
    now = datetime.datetime.now()
    time = db.get("lastsalary", ctx.author.id)

    if not time:
        time = now - datetime.timedelta(days=10)
    else:
        time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")

    if time + datetime.timedelta(days=1) < now:
        db.give_item(ctx.author.id, 1, 1)
        db.update_bal(ctx.author.id, 500)
        db.set("lastsalary", ctx.author.id, datetime.datetime.strftime(now, "%Y-%m-%dT%H:%M:%S"))

        lootbox = index.get_by_id(1)
        money = index.get_by_id(0)
        await ctx.send(f"""{ctx.author.mention}: Aight, here's your daily salary: 500 {money.emoji} and a {str(lootbox)}""")
    else:
        await ctx.send(f"""Leave me alone, you've already had your salary today!\nNext salary can be claimed in `{''.join(str(time + datetime.timedelta(days=1) - now).split('.')[:1])}`""")


async def int_gamble(ctx, amount: int, odds):
    authbal = db.get_bal(ctx.author.id)

    if amount > 1000 or amount < -1000:
        await ctx.send("You can't gamble more than 1000 points at a time")
        return False

    if amount == 0:
        await ctx.send("Thats not gonna work m8")
        return False
    elif amount > 0:
        if authbal < amount:
            await ctx.send("You can't gamble what you don't have")
            return False
    else:
        if authbal > amount:
            await ctx.send("You can't gamble what you don't have")
            return False

    if random.choices([True, False], odds)[0]:
        db.update_bal(ctx.author.id, amount)
        embed = discord.Embed(title="You won!", description=f"Your bet was doubled!\nOdds: {odds[0]}%\n**New balance:** {db.get_bal(ctx.author.id)} <:coin:632592319245451286>", colour=discord.Colour(0x70a231))
    else:
        db.update_bal(ctx.author.id, -amount)
        embed = discord.Embed(title="You lost!", description=f"This is so sad...\nOdds: {odds[0]}%\n**New balance:** {db.get_bal(ctx.author.id)} <:coin:632592319245451286>", colour=discord.Colour(0x70a231))

    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
    await ctx.send(embed=embed)

    return True


@client.command(aliases=["bet", "casino"])
async def gamble(ctx, amount=None):
    """Come on, have a try. You have a 50% chance to double your bet"""
    if not amount:
        await ctx.send("How much to gamble?")
        return
    try:
        amount = int(amount)
    except ValueError:
        await ctx.send("Thats not number tho")
        return
        
    
    odds = [50, 50]

    await int_gamble(ctx, amount, odds)


@gamble.error
async def gamble_error(ctx, error):
    await ctx.send("Please enter an amount, you have a 50% chance to double your bet")


@client.command(aliases=["inv", "items"])
async def inventory(ctx, *args):
    """SHOW ME WHAT YOU GOT"""
    member = await getmember(ctx, args)

    embed = discord.Embed(title="Inventory:", colour=discord.Colour(0x70a231))
    embed.set_author(name=member.name, icon_url=member.avatar_url)
    inv = db.get_inv(member.id)
    if inv == []:
        embed.title = "Inventory empty..."
    else:
        for item in inv:
            itemobj = index.get_by_id(item[0])
            embed.add_field(name=itemobj.emoji, value=f"""{item[1]}x {itemobj.name}""", inline=True)
    await ctx.send(embed=embed)    


@client.command()
@commands.is_owner()
async def gimme(ctx, giv: int, user=None):
    if user:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(user)
        if not member:
            await ctx.send("I don't know them")
            return
    else:
        member = ctx.author
    item = index.get_by_id(giv)
    db.give_item(member.id, item.id, 1)
    await ctx.send(f"""{member.mention}: i got u one of them {str(item)}, you filthy cheater""")


@client.command()
@commands.is_owner()
async def gimmecash(ctx, giv: int, user=None):
    if user:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(user)
        if not member:
            await ctx.send("I don't know them")
            return
    else:
        member = ctx.author
    db.update_bal(member.id, giv)
    await ctx.send(f"""{member.mention}: i got u some of them cash, you filthy cheater""")


@client.command()
@commands.is_owner()
async def createcounter(ctx, year: int, month: int, day: int, hour: int):
    time = datetime.datetime(year, month, day, hour).isoformat()
    message = await ctx.send("counter")
    counters.append({
        "time": time, 
        "guild": message.guild.id, 
        "channel": message.channel.id,
        "message": message.id
    })
    with open("counters.json", "w") as f:
        json.dump(counters, f, indent=4)


@client.command(aliases=["info", "tellmemore"])
async def iteminfo(ctx, *, item=""):
    """U wanna know what some of this shit does?"""
    if not item:
        await ctx.send("What item do u wanna know about?")
        return
    item = index.get_by_alias(item)
    if item and item.longdesc:
        embed = discord.Embed(title=str(item), description=item.longdesc, colour=discord.Colour(0x70a231))
        embed.set_author(name=client.user.name, icon_url=client.user.avatar_url)
        if item.id == 1:
            maxweight = 0
            for iitem in index.items:
                maxweight += iitem.lootboxweight
            for iitem in index.items:
                if iitem.lootboxweight:
                    embed.add_field(name=str(iitem), value=f"Chance: {round(iitem.lootboxweight / maxweight * 100, 2)}%", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("That item does not exist...")


@iteminfo.error
async def iteminfo_error(ctx, error):
    await ctx.send("Please specify an item.")


@client.command(aliases=["open", "eat"])
async def use(ctx, *args):
    """Do something with your random crap"""
    authorid = ctx.author.id

    if not args:
        await ctx.send("Pls tell me item thx")
        return

    item = index.get_by_alias(args[0])
    if not item or not item.use:
        await ctx.send("Unknown item that")
        return

    if not db.has_item(authorid, item.id):
        await ctx.send("You dont own that shit man")
        return

    if item.useargs == "m":
        if len(args) == 1:
            await ctx.send("Please tell me who to use this shit on aight?")
            return
        else:
            if ctx.message.mentions:
                member = ctx.message.mentions[0]
            else:
                member = ctx.guild.get_member_named(args[1])
            if not member:
                await ctx.send("Thats not person tho")
                return

        rmitem = await item.use(ctx, member)
    elif item.useargs == "i":
        if len(args) == 1:
            await ctx.send("How much to gamble?") # change this later
            return
        try:
            amount = int(args[1])
        except ValueError:
            await ctx.send("Thats not number tho")
            return
        
        rmitem = await item.use(ctx, amount)
    else:
        rmitem = await item.use(ctx)

    if rmitem:
        db.rem_item(authorid, item.id)


@client.command(aliases=["xp"])
async def level(ctx, *args):
    """Is this an mmorpg or somethin?"""
    member = await getmember(ctx, args)

    level = db.get("level", member.id)
    xp = db.get("xp", member.id)
        
    if member == ctx.author:
        await ctx.send(f"""{member.mention}: Yeah boi, u r level `{level}` & ur `{xp}/{levelcost}` to the next level""")
    else:
        await ctx.send(f"""{member.mention}: Is level `{level}` & theyr `{xp}/{levelcost}` to the next level""")


@client.command(aliases=["richest", "leaderboard"])
async def baltop(ctx):
    """See who to rob"""
    top = []
    for userid in db.all_users():
        top.append((userid, db.get_bal(userid)))
    top = sorted(top, key=operator.itemgetter(1))[::-1]
    embed = discord.Embed(title="Top 10 points:", description="━━━━━━━━━━━━━━━", colour=discord.Colour(0x70a231))
    amount = 0
    for user in top:
        if top.index(user) < (amount + 10):
            if ctx.guild.get_member(int(user[0])):
                embed.add_field(name=str(top.index(user) + 1 - amount) + ". " + ctx.guild.get_member(int(user[0])).display_name, value=f"""{user[1]} <:coin:632592319245451286>""", inline=False)
            else:
                amount += 1
    await ctx.send(embed=embed)


@client.command(aliases=["toprank"])
async def ranks(ctx):
    """See who to rob"""
    top = []
    for userid in db.all_users():
        top.append((userid, db.get("level", userid)))
    top = sorted(top, key=operator.itemgetter(1))[::-1]
    embed = discord.Embed(title="Top 10 levels:", description="━━━━━━━━━━━━━━━", colour=discord.Colour(0x70a231))
    amount = 0
    for user in top:
        if top.index(user) < (amount + 10):
            if ctx.guild.get_member(int(user[0])):
                embed.add_field(name=str(top.index(user) + 1 - amount) + ". " + ctx.guild.get_member(int(user[0])).display_name, value=f"""level: {user[1]}""", inline=False)
            else:
                amount += 1
    await ctx.send(embed=embed)


@client.command(aliases=["coin"])
async def coinflip(ctx):
    """I think its pretty self-explanatory tbh"""
    await ctx.send(random.choice(["Heads!", "Tails!"]))


@client.command(aliases=["choice"])
async def choose(ctx, *args):
    """I think its pretty self-explanatory tbh"""
    if len(args) > 1:
        await ctx.send(random.choice(args))
    else:
        await ctx.send("come on, gimme somethin to work with here...")


@client.command(aliases=["buy"])
async def shop(ctx, buythis=None, amount=1):
    """Yo whattup come buy some stuffs"""
    if not buythis:
        embed = discord.Embed(title="For sale:", colour=discord.Colour(0x70a231))
        embed.set_author(name="yo whattup come buy some stuffs", icon_url=client.user.avatar_url)
        for item in index.items:
            if item.buy and item.description:
                embed.add_field(name=f"**{str(item)}** - {item.buy} Points", value=item.description, inline=False)
        await ctx.send(embed=embed)
        return

    item = index.get_by_alias(buythis)
    if not item:
        await ctx.send("I don't sell that")
        return

    if db.get_bal(ctx.author.id) >= item.buy * amount:
        await ctx.send(f"{ctx.author.mention}: you bought {amount} {str(item)} for {item.buy * amount} <:coin:632592319245451286>")
        db.update_bal(ctx.author.id, -(item.buy * amount))
        db.give_item(ctx.author.id, item.id, amount)
    else:
        await ctx.send("U ain't got da cash m8")


@client.command(aliases=["sellitem"])
async def sell(ctx, sellthis, amount=1):
    """Yo whattup come buy some stuffs"""
    item = index.get_by_alias(sellthis)
    if not item:
        await ctx.send("I don't buy that")
        return

    if not db.has_item(ctx.author.id, item.id, amount):
        await ctx.send("You dont own that shit man")
        return

    await ctx.send(f"{ctx.author.mention}: you sold {amount} {str(item)} for {item.sell * amount} <:coin:632592319245451286>")
    db.update_bal(ctx.author.id, item.sell * amount)
    db.rem_item(ctx.author.id, item.id, amount)


@client.command()
async def helpiminfuckingdebt(ctx):
    bal = db.get_bal(ctx.author.id)
    if bal < 0:
        await ctx.send("ur in some deep shit my dude, lemme help u out")
        db.update_bal(ctx.author.id, -bal)
    else:
        await ctx.send("no ur not")

#================================= item quick-commands =================================#

@client.command()
async def rob(ctx, arg1):
    await use(ctx, "mask", arg1)

@client.command()
async def nuke(ctx, arg1):
    await use(ctx, "nuke", arg1)

@client.command()
async def nuke2(ctx, arg1):
    await use(ctx, "nuke2", arg1)

#================================= /item quick-commands ================================#


#=================================== trubot section ====================================#


@trubot.command()
async def tru(ctx):
    await ctx.send(f"> **Enabling TruBot v{truversion}**")
    for i in range(3):
        await asyncio.sleep(1)
        await ctx.send("> **.**")
    await ctx.send("> **Tru**")
    await ctx.send(f"> **Disabling TruBot v{truversion}**")
    await asyncio.sleep(2)
    await ctx.send(f"> **Goodbye**")


#================================== \trubot section ====================================#


if channelid:
    bgtask = client.loop.create_task(background())
bgtask2 = client.loop.create_task(background2())
#client.run(token)

loop = asyncio.get_event_loop()
loop.create_task(client.start(token))
if enabletrubot:
    loop.create_task(trubot.start(trutoken))
loop.run_forever()