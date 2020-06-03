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
client = commands.Bot(command_prefix=("plzz ", "Plzz ", "plz ", "Plz "))

# custom imports
from itemindex import Item, ItemIndex

lastid = {}

config = configparser.ConfigParser()
config.read_file(open("config.conf", "r"))
token = config.get("config", "token")
channelid = config.get("config", "triviachannel")
triviaminwait = int(config.get("config", "triviaminwait"))
triviamaxwait = int(config.get("config", "triviamaxwait"))
index = ItemIndex("main")

#read "database"
with open("scores.json", "r") as f:
    scores = json.load(f)
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
    "uno": "<:unoreverse:699194687646597130>",
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
        print(i)
        weights = []
        for item in index.items:
            weights.append(item.lootboxweight)
        addthis = random.choices(index.items, weights)[0]
        amount = random.randint(1, addthis.lootboxmax)
        #addthis = str(addthis)
        if addthis.id == 0:
            embed.add_field(name="<:coin:632592319245451286>", value=f"{amount} Points", inline=True)
            scores[str(ctx.author.id)]["score"] += amount
        else:
            embed.add_field(name=addthis.emoji, value=f"{amount}x {addthis.name}", inline=True)
            await giveitem(ctx.author, addthis.json(), amount)
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


async def item_dice(ctx):
    """
    Using this before gambling increases your chance of winning to 66%.
    (Don't use this at a real casino, cus i think thats illegal)

    *\* this is janky will rework soon(tm)*
    """
    scores[str(ctx.author.id)]["effects"]["dice"] = 1
    await ctx.send(ctx.author.mention + ": used item")
    return True

index.add(
    use=item_dice,
    name="Loaded Dice",
    emoji="<:dice:632295947552030741>",
    aliases=[],
    description="Give luck some help while gambling, one use (will rework this)",
    lootboxmax=3,
    lootboxweight=1000,
    buy=200,
    sell=100
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
    scores[str(member.id)]["score"] -= amount
    scores[str(ctx.author.id)]["score"] += amount # add cooldown?
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
    if scores[str(member.id)]["score"] >= 300:
        amount = random.randint(40, 300)
    elif scores[str(member.id)]["score"] < 50:
        amount = 0
    else:
        amount = random.randint(40, scores[str(member.id)]["score"])
    if amount:
        if "uno" in scores[str(member.id)]["effects"]:
            amount = int(amount / 2)
            scores[str(member.id)]["score"] += amount
            scores[str(ctx.author.id)]["score"] -= amount
            await ctx.send(ctx.author.mention + f": You robbed {member.mention}, but they had an uno reverse card active! you lost `{amount}` points!")
            await remeffect(member.id, "uno")
        elif "vault" in scores[str(member.id)]["effects"]:
            await ctx.send(ctx.author.mention + f": You robbed {member.mention}, but they had a vault active and you lost your mask!")
            await remeffect(member.id, "vault")
        else:
            scores[str(member.id)]["score"] -= amount
            scores[str(ctx.author.id)]["score"] += amount
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
    scores[str(ctx.author.id)]["score"] -= 10
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
        cash = random.randint(5, 30)
        await ctx.send(ctx.author.mention + f""": There were also {cash} <:coin:632592319245451286> hidden inside!""")
        scores[str(ctx.author.id)]["score"] += cash
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
    if scores[str(member.id)]["score"] >= 500:
        amount = random.randint(0, 500)
    elif scores[str(member.id)]["score"] < 0:
        amount = random.randint(0, scores[str(member.id)]["score"] * -1) * -1
    elif scores[str(member.id)]["score"] < 500:
        amount = random.randint(0, scores[str(member.id)]["score"])
    if "uno" in scores[str(member.id)]["effects"]:
        amount = int(amount / 2)
        scores[str(member.id)]["score"] += int(amount / 2)
        scores[str(ctx.author.id)]["score"] -= amount
        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, but they had an uno reverse card active! you lost `{amount}` points, and half of them were destroyed!")
        await remeffect(member.id, "uno")
    elif "vault" in scores[str(member.id)]["effects"]:
        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, but they had a vault active!")
        await remeffect(member.id, "vault")
    else:
        scores[str(member.id)]["score"] -= amount
        scores[str(ctx.author.id)]["score"] += int(amount / 2)
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
    if scores[str(member.id)]["score"] >= 1000:
        amount = random.randint(400, 1000)
    elif scores[str(member.id)]["score"] < 0:
        amount = random.randint(0, scores[str(member.id)]["score"] * -1)
    elif scores[str(member.id)]["score"] < 1000:
        amount = random.randint(int(scores[str(member.id)]["score"] * 0.4), scores[str(member.id)]["score"])
    if "uno" in scores[str(member.id)]["effects"]:
        amount = int(amount / 2)
        scores[str(member.id)]["score"] += int(amount / 2)
        scores[str(ctx.author.id)]["score"] -= amount
        await ctx.send(ctx.author.mention + f": You yeeted a nuke 2: electric boogaloo at {member.mention}, but they had an uno reverse card active! you lost `{amount}` points, and half of them were destroyed!")
        await remeffect(member.id, "uno")
    elif "vault" in scores[str(member.id)]["effects"]:
        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, but they had a vault active!")
        await remeffect(member.id, "vault")
    else:
        scores[str(member.id)]["score"] -= amount
        scores[str(ctx.author.id)]["score"] += int(amount / 2)
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


async def item_uno(ctx):
    """
    Okay so we're playing uno now apparently,
    this acually seems pretty useful though.

    The uno card can reverse a single rob or nuke.
    After that it just disappears. like, \*poof\*, and its gone.

    *\* this item is pretty good at keeping you safe, if you can afford it...*
    """
    if "uno" in scores[str(ctx.author.id)]["effects"]:
        await ctx.send(ctx.author.mention + f""": You already an uno card active""")
        return False
    else:
        await ctx.send(ctx.author.mention + f""": Uno Reverse Card activate! you are now protected from one rob/nuke""")
        scores[str(ctx.author.id)]["effects"]["uno"] = 1
    return True

index.add(
    use=item_uno,
    name="Uno Reverse Card",
    emoji="<:unoreverse:699194687646597130>",
    aliases=[],
    description="Use this to ward off those pesky thieves once and for all",
    lootboxmax=1,
    lootboxweight=40,
    buy=1200,
    sell=800
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
    if "vault" in scores[str(ctx.author.id)]["effects"]:
        if scores[str(ctx.author.id)]["effects"]["vault"] < 3:
            scores[str(ctx.author.id)]["effects"]["vault"] += 1
        else:
            await ctx.send(ctx.author.mention + f""": You already have 3 vaults active""")
            return False
    else:
        scores[str(ctx.author.id)]["effects"]["vault"] = 1
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
    if "vault" in scores[str(member.id)]["effects"]:
        await remeffect(member.id, "vault")
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

#=================================== /item defintions ==================================#

print("connecting...")


def check(payload):
    return payload.channel_id == int(channelid) and not payload.user_id == client.user.id

async def save():
    with open("scores.json", "w") as f:
        json.dump(scores, f, indent=4)

async def modscore(user, amount):
    scores[str(user.id)]["score"] += amount

async def equal_dicts(a, b, ignore_keys):
    ka = set(a).difference(ignore_keys)
    kb = set(b).difference(ignore_keys)
    return ka == kb and all(a[k] == b[k] for k in ka)

async def giveitem(user, item, amount):
    userid = str(user.id)
    add = False
    for ownitem in scores[userid]["items"]:
        if item["id"] == ownitem["id"]:
            ownitem["count"] += amount
            add = True
            break
    if not add:
        item["count"] = amount
        scores[userid]["items"].append(item)

async def hasitem(userid, item):
    found = False
    for iitem in scores[str(userid)]["items"]:
        if iitem["id"] == item.id:
            found = scores[str(userid)]["items"].index(iitem)
            break
    return found

async def remeffect(userid: str, effect):
    userid = str(userid)
    if scores[userid]["effects"][effect] > 1:
        scores[userid]["effects"][effect] -= 1
    else:
        del scores[userid]["effects"][effect]

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
                memberidstr = str(member.id)
                if memberidstr in scores:
                    if "score" in scores[memberidstr]:
                        scores[memberidstr]["score"] += points
                    else:
                        scores[memberidstr]["score"] = points
                else:
                    scores[memberidstr] = {}
                    scores[memberidstr]["score"] = points
                if random.randint(1, 10) == 1:
                    lootbox = index.get_by_id(1)
                    await giveitem(member, lootbox.json(), 1)
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

async def background3():
    await client.wait_until_ready()
    print("background3 active")
    while True:
        await asyncio.sleep(60)
        print("saving data...")
        await save()

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

@client.event
async def on_disconnect():
    print("saving data for disconnect...")
    await save()

@client.event
async def on_message(message):
    if not message.author.id == client.user.id:
        if not str(message.channel.id) in lastid:
            lastid[str(message.channel.id)] = 0
        if not message.author.id == lastid[str(message.channel.id)]:
            lastid[str(message.channel.id)] = message.author.id
            if not str(message.author.id) in scores:
                scores[str(message.author.id)] = {}
            if not "xp" in scores[str(message.author.id)]:
                scores[str(message.author.id)]["xp"] = 0
            if not "level" in scores[str(message.author.id)]:
                scores[str(message.author.id)]["level"] = 1
            if not "items" in scores[str(message.author.id)]:
                scores[str(message.author.id)]["items"] = [{
                "displayname": "Loot Box",
                "emoji": "<:lootbox:632286669592199217>",
                "id": 1,
                "count": 3
            }]
            if not "effects" in scores[str(message.author.id)]:
                scores[str(message.author.id)]["effects"] = {}
            if not "score" in scores[str(message.author.id)]:
                scores[str(message.author.id)]["score"] = 0
            scores[str(message.author.id)]["xp"] += 1
            if scores[str(message.author.id)]["xp"] >= levelcost:
                scores[str(message.author.id)]["xp"] = 0
                scores[str(message.author.id)]["level"] += 1
                lootbox = index.get_by_id(1)
                await message.channel.send(f"""{message.author.mention}: Holy shit, you leveled up! Now level `{scores[str(message.author.id)]["level"]}`""")
                await message.channel.send(f"{message.author.mention}: Wow, you found a {str(lootbox)}!")
                await giveitem(message.author, lootbox.json(), 1)
    await client.process_commands(message)

@client.command(aliases=["bal", "money", "status"])
async def points(ctx, *args):
    """CAPITALISM BOYS"""
    if len(args) == 1:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(args[0])
    else:
        member = ctx.author

    if not member:
        await ctx.send("I don't know them")
        return

    vaults = []
    if "vault" in scores[str(member.id)]["effects"]:
        vaultsnum = scores[str(member.id)]["effects"]["vault"]
    else:
        vaultsnum = 0

    for i in range(vaultsnum):
        print(i)
        vaults.append("<:vault:699266653791322172>")
    for i in range(3 - vaultsnum):
        print(i)
        vaults.append("⭕")
    if "uno" in scores[str(member.id)]["effects"]:
        vaults.append("(<:unoreverse:699194687646597130>)")
    vaults = " ".join(vaults)

    embed = discord.Embed(title="Status:", description=f"{scores[str(member.id)]['score']} <:coin:632592319245451286>\n**Active vaults:**\n{vaults}", colour=discord.Colour(0x70a231))
    embed.set_author(name=member.name, icon_url=member.avatar_url)
    await ctx.send(embed=embed)

@client.command()
async def mclink(ctx, mcacc: str):
    """For the Minceraft server, enter your username and buy ingame items with your points (not microtransactions)"""
    if not str(ctx.author.id) in scores:
        scores[str(ctx.author.id)] = {}
    id = 0
    for key, value in scores.items():
        if "mcacc" in value and value["mcacc"].lower() == mcacc.lower():
            id = int(key)
            break
    if id:
        await ctx.send("That account is already linked, if this is really your Minecraft account please contact enjarai")
    else:
        scores[str(ctx.author.id)]["mcacc"] = mcacc
        await ctx.send("Database updated!")

@client.command(aliases=["bet", "casino"])
async def gamble(ctx, amount: int):
    """Come on, have a try. You have a 50% chance to double your bet"""
    if amount < 1:
        await ctx.send("nice try")
        return
    if str(ctx.author.id) in scores and "score" in scores[str(ctx.author.id)] and scores[str(ctx.author.id)]["score"] >= amount:
        if "dice" in scores[str(ctx.author.id)]["effects"]:
            await ctx.send("wow man! you have an active Loaded Dice, your chance of winning is 66% instead of 50%")
            randbool = random.choice([True, True, False])
            if scores[str(ctx.author.id)]["effects"]["dice"] > 1:
                scores[str(ctx.author.id)]["effects"]["dice"] -= 1
            else:
                del scores[str(ctx.author.id)]["effects"]["dice"]
        else:
            randbool = random.choice([True, False])
        if randbool:
            scores[str(ctx.author.id)]["score"] += amount
            await ctx.send("You won! Your bet was doubled!\nNew balance: `{}`".format(scores[str(ctx.author.id)]["score"]))
        else:
            scores[str(ctx.author.id)]["score"] -= amount
            await ctx.send("You lost! This is so sad...\nNew balance: `{}`".format(scores[str(ctx.author.id)]["score"]))
    else:
        await ctx.send("You can't gamble what you don't have")

@gamble.error
async def gamble_error(ctx, error):
    await ctx.send("Please enter an amount, you have a 50% chance to double your bet")

@client.command(aliases=["inv", "items"])
async def inventory(ctx, *args):
    """SHOW ME WHAT YOU GOT"""
    if len(args) == 1:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(args[0])
        if not member:
            await ctx.send("I don't know them")
            return
    else:
        member = ctx.author
    embed = discord.Embed(title="Inventory:", colour=discord.Colour(0x70a231))
    embed.set_author(name=member.name, icon_url=member.avatar_url)
    if scores[str(member.id)]["items"] == []:
        embed.title = "Inventory empty..."
    else:
        for item in scores[str(member.id)]["items"]:
            embed.add_field(name=item["emoji"], value=f"""{item["count"]}x {item["displayname"]}""", inline=True)
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
    await giveitem(member, item.json(), 1)
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
    scores[str(member.id)]["score"] += giv
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
    authoridstr = str(authorid)

    if not args:
        await ctx.send("Pls tell me item thx")
        return

    item = index.get_by_alias(args[0])
    if not item:
        await ctx.send("Unknown item that")
        return

    has = await hasitem(authorid, item)
    if isinstance(has, bool):
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
    else:
        rmitem = await item.use(ctx)

    if rmitem:
        if scores[authoridstr]["items"][has]["count"] > 1:
            scores[authoridstr]["items"][has]["count"] -= 1
        else:
            del scores[authoridstr]["items"][has]

@use.error
async def use_error(ctx, error):
    await ctx.send("Internal error: " + str(error))

@client.command(aliases=["xp"])
async def level(ctx, *args):
    """Is this an mmorpg or somethin?"""
    if len(args) == 1:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(args[0])
        if member:
            await ctx.send(f"""{member.mention}: Is level `{scores[str(member.id)]["level"]}` & theyr `{scores[str(member.id)]["xp"]}/{levelcost}` to the next level""")
        else:
            await ctx.send("I don't know them")
    else:
        await ctx.send(f"""{ctx.author.mention}: Yeah boi, u r level `{scores[str(ctx.author.id)]["level"]}` & ur `{scores[str(ctx.author.id)]["xp"]}/{levelcost}` to the next level""")

@client.command(aliases=["richest", "leaderboard"])
async def baltop(ctx):
    """See who to rob"""
    top = []
    for userid in scores:
        top.append((userid, scores[userid]["score"]))
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

@client.command(aliases=["coin"])
async def coinflip(ctx):
    """I think its pretty self-explanatory tbh"""
    if random.choice([True, False]):
        await ctx.send("Heads!")
    else:
        await ctx.send("Tails!")

@client.command(aliases=["buy"])
async def shop(ctx, buythis=None, amount=1):
    """Yo whattup come buy some stuffs"""
    if not buythis:
        embed = discord.Embed(title="For sale:", colour=discord.Colour(0x70a231))
        embed.set_author(name="yo whattup come buy some stuffs", icon_url=client.user.avatar_url)
        for item in index.items:
            if item.buy:
                embed.add_field(name=f"**{str(item)}** - {item.buy} Points", value=item.description, inline=False)
        await ctx.send(embed=embed)
        return

    item = index.get_by_alias(buythis)
    if not item:
        await ctx.send("I don't sell that")
        return

    if scores[str(ctx.author.id)]["score"] >= item.buy * amount:
        await ctx.send(f"{ctx.author.mention}: you bought {amount} {str(item)}")
        scores[str(ctx.author.id)]["score"] -= item.buy * amount
        await giveitem(ctx.author, item.json(), amount)
    else:
        await ctx.send("U ain't got da cash m8")
                
@client.command(aliases=["sellitem"])
async def sell(ctx, sellthis, amount=1):
    """Yo whattup come buy some stuffs"""
    item = index.get_by_alias(sellthis)
    if not item:
        await ctx.send("I don't buy that")
        return

    has = await hasitem(ctx.author.id, item)
    if isinstance(has, bool):
        await ctx.send("You dont own that shit man")
        return

    if not scores[str(ctx.author.id)]["items"][has]["count"] >= amount:
        await ctx.send("You dont have enough of that shit")
        return

    await ctx.send(f"{ctx.author.mention}: you sold {amount} {str(item)} for {item.sell * amount} <:coin:632592319245451286>")
    scores[str(ctx.author.id)]["score"] += item.sell * amount
    if scores[str(ctx.author.id)]["items"][has]["count"] > amount:
        scores[str(ctx.author.id)]["items"][has]["count"] -= amount
    else:
        del scores[str(ctx.author.id)]["items"][has]

@client.command()
async def helpiminfuckingdebt(ctx):
    if scores[str(ctx.author.id)]["score"] < 0:
        await ctx.send("ur in some deep shit my dude, lemme help u out")
        scores[str(ctx.author.id)]["score"] = 0
    else:
        await ctx.send("no ur not")

if channelid:
    bgtask = client.loop.create_task(background())
bgtask2 = client.loop.create_task(background2())
bgtask3 = client.loop.create_task(background3())
client.run(token)
