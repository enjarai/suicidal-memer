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
client = commands.Bot(command_prefix=("plzz ", "Plzz ", "plz ", "Plz "))

global lastid
lastid = {}

config = configparser.ConfigParser()
config.read_file(open("config.conf", "r"))
token = config.get("config", "token")
channelid = config.get("config", "triviachannel")

#read "database"
with open("scores.json", "r") as f:
    scores = json.load(f)

qdir = glob.glob("./questions/*.json")
questions = []
for i in qdir:
    with open(i, "r") as f:
        q = json.load(f)
    questions.append(q)

triviamultiplier = 10
levelcost = 60
lootboxtemplate = {
    "displayname": "Loot Box",
    "emoji": "<:lootbox:632286669592199217>",
    "id": 1
}
loadeddice = {
    "displayname": "Loaded Dice",
    "emoji": "<:dice:632295947552030741>",
    "id": 2
}
spambot = {
    "displayname": "Spambot",
    "emoji": "<:spambot:632466831063646221>",
    "id": 3
}
robbersmask = {
    "displayname": "Robbers Mask",
    "emoji": "<:balaclava:632658938437042212>",
    "id": 4
}
moldybread = {
    "displayname": "Moldy Bread",
    "emoji": "<:moldybread:632921575649443909>",
    "id": 5
}
fortunecookie = {
    "displayname": "Fortune Cookie",
    "emoji": "<:fortunecookie:633286682195525653>",
    "id": 6
}
nuke = {
    "displayname": "Nuke",
    "emoji": "<:nuke:671718044078440448>",
    "id": 7,
}

itemaliases = {
    "1": ["lootbox", "loot box", "loot"],
    "2": ["dice", "loaded dice", "loadeddice"],
    "3": ["bot", "spam", "spambot", "spam bot"],
    "4": ["mask", "robber", "robbersmask", "robbers mask", "robbermask"],
    "5": ["bread", "moldy", "moldybread", "moldy bread"],
    "6": ["fortune", "cookie", "fortunecookie", "fortune cookie"],
    "7": ["nuke", "big boom"]
}
itemdescriptions = {
    "1": "Some say it's gambling, so imma add it while it's legal...",
    "2": "Give luck some help while gambling, one time use.",
    "3": "Anyone here remember 'tako, dmspam'?",
    "4": "Use this to steal some points from your buddies, i'm sure they won't hate you...",
    "5": "Why would you keep this?",
    "6": "Shows you your true fortune!",
    "7": "Kim jong un wants to know your location. this item steals up to 500 points from anyone, but half of them are always destroyed"
}
itemmax = {
    "0": 200,
    "2": 3,
    "3": 5,
    "4": 1,
    "5": 1,
    "6": 10,
    "7": 1
}
itemindex = {
    "1": lootboxtemplate,
    "2": loadeddice,
    "3": spambot,
    "4": robbersmask,
    "5": moldybread,
    "6": fortunecookie,
    "7": nuke
}
shopcosts = {
    "1": 500,
    "2": 200,
    "3": 100,
    "4": 400,
    "5": 20,
    "6": 80,
    "7": 1000
}

print("connecting...")


def check(reaction, user):
    return reaction.message.channel == client.get_channel(int(channelid)) and not user.id == client.user.id

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

async def hasitem(scores, userid, itemid):
    found = False
    for item in scores[str(userid)]["items"]:
        if item["id"] == itemid:
            found = scores[str(userid)]["items"].index(item)
            break
    return found

async def background():
    await client.wait_until_ready()
    channel = client.get_channel(int(channelid))
    while True:
        slp = random.randint(360, 600)
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
            ua = await client.wait_for("reaction_add", check=check)
            if emoji.demojize(ua[0].emoji, use_aliases=True) in q["correct"]:
                points = (10 - (2 * tries)) * triviamultiplier
                embed=discord.Embed(description="🟢 {} has earned {} points!".format(ua[1], points))
                await channel.send(embed=embed)
                if str(ua[1].id) in scores:
                    if "score" in scores[str(ua[1].id)]:
                        scores[str(ua[1].id)]["score"] += points
                    else:
                        scores[str(ua[1].id)]["score"] = points
                else:
                    scores[str(ua[1].id)] = {}
                    scores[str(ua[1].id)]["score"] = points
                if random.randint(1, 10) == 1:
                    await giveitem(ua[1], lootboxtemplate, 1)
                    await channel.send(f"{ua[1].mention}: Wow, you found a loot box!")
                break
            else:
                if tries < 4:
                    tries += 1
                embed=discord.Embed(description="🔴 {} has answered wrongly!".format(ua[1]))
                await channel.send(embed=embed)

async def background2():
    await client.wait_until_ready()
    print("background2 active")
    while True:
        await asyncio.sleep(60)
        print("effect tick...")
        for user in scores:
            if not "effects" in scores[user]:
                scores[user]["effects"] = {}
            if not scores[user]["effects"] == {}:
                delete = []
                for effect in scores[user]["effects"]:
                    if scores[user]["effects"][effect] > 1:
                        scores[user]["effects"][effect] -= 1
                    else:
                        delete.append(effect)
                if delete:
                    for thing in delete:
                        del scores[user]["effects"][thing]

async def background3():
    await client.wait_until_ready()
    print("background3 active")
    while True:
        await asyncio.sleep(60)
        print("saving data...")
        await save()

@client.event
async def on_disconnect():
    print("saving data for disconnect...")
    await save()

@client.event
async def on_message(message):
    global lastid
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
                await message.channel.send(f"""{message.author.mention}: Holy shit, you leveled up! Now level `{scores[str(message.author.id)]["level"]}`""")
                await message.channel.send(f"{message.author.mention}: Wow, you found a loot box!")
                await giveitem(message.author, lootboxtemplate, 1)
    await client.process_commands(message)

@client.command(aliases=["bal", "money"])
async def points(ctx, *args):
    """𝅘𝅥𝅮  it's all about the money, money, money 𝅘𝅥𝅮 """
    if len(args) == 1:
        if ctx.message.mentions:
            member = ctx.message.mentions[0]
        else:
            member = ctx.guild.get_member_named(args[0])
        if member:
            await ctx.send("{}: hav got `{}` points!".format(member.mention, scores[str(member.id)]["score"]))
        else:
            await ctx.send("I don't know them")
    else:
        await ctx.send("{}: u got `{}` points!".format(ctx.author.mention, scores[str(ctx.author.id)]["score"]))

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
    await giveitem(member, itemindex[str(giv)], 1)
    await ctx.send(f"""{member.mention}: i got u one of them {itemindex[str(giv)]["displayname"]}, you filthy cheater""")

@client.command(aliases=["info", "tellmemore"])
async def iteminfo(ctx, *, item: str):
    """U wanna know what some of this shit does?"""
    itemid = ""
    for key, alis in itemaliases.items():
        if item in alis:
            itemid = key
    if itemid:
        await ctx.send(itemdescriptions[itemid])
    else:
        await ctx.send("That item does not exist...")

@iteminfo.error
async def iteminfo_error(ctx, error):
    await ctx.send("Please specify an item.")

@client.command(aliases=["open", "eat"])
async def use(ctx, *args):
    """Do something with your random crap"""
    if args:
        if len(args) == 1:
            if args[0] in itemaliases["1"]:
                has = await hasitem(scores, ctx.author.id, 1)
                if not isinstance(has, bool):
                    #insert loot box code here
                    embed = discord.Embed(title="Loot Box opened!", description="You got:", colour=discord.Colour(0x70a231))
                    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    for i in range(3):
                        print(i)
                        addthis = random.choice(list(itemmax.keys()))
                        amount = random.randint(1, itemmax[addthis])
                        if addthis == "0":
                            embed.add_field(name="<:coin:632592319245451286>", value=f"""{amount} Points""", inline=True)
                            scores[str(ctx.author.id)]["score"] += amount
                        else:
                            embed.add_field(name=itemindex[addthis]["emoji"], value=f"""{amount}x {itemindex[addthis]["displayname"]}""", inline=True)
                            await giveitem(ctx.author, itemindex[addthis], amount)
                    await ctx.send(embed=embed)
                    #----------------------
                    if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                        scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                    else:
                        del scores[str(ctx.author.id)]["items"][has]
                else:
                    await ctx.send("You don't have that item...")
            elif args[0] in itemaliases["2"]:
                has = await hasitem(scores, ctx.author.id, 2)
                if not isinstance(has, bool):
                    scores[str(ctx.author.id)]["effects"]["dice"] = 1
                    if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                        scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                    else:
                        del scores[str(ctx.author.id)]["items"][has]
                    await ctx.send(ctx.author.mention + ": used item")
                    # await ctx.send("sorry, this item has been deemed to OP and is temp banned")
                else:
                    await ctx.send("You don't have that item...")
            elif args[0] in itemaliases["3"]:
                await ctx.send("You need to specify someone to spam.")
            elif args[0] in itemaliases["4"]:
                await ctx.send("You need to specify someone to steal from.")
            elif args[0] in itemaliases["5"]:
                has = await hasitem(scores, ctx.author.id, 5)
                if not isinstance(has, bool):
                    await ctx.send(ctx.author.mention + ": You ate the Moldy Bread, why the fuck would you do that? *backs away slowly*\nU got -10 <:coin:632592319245451286> cus thats just nasty")
                    scores[str(ctx.author.id)]["score"] -= 10
                    if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                        scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                    else:
                        del scores[str(ctx.author.id)]["items"][has]
                else:
                    await ctx.send("You don't have that item...")
            elif args[0] in itemaliases["6"]:
                has = await hasitem(scores, ctx.author.id, 6)
                if not isinstance(has, bool):
                    await ctx.send(ctx.author.mention + f""": You cracked open the cookie, the little piece of paper inside says:\n```{subprocess.check_output(["/usr/games/fortune"]).decode("utf-8")}```""")
                    if random.randint(1, 10) == 1:
                        cash = random.randint(5, 30)
                        await ctx.send(ctx.author.mention + f""": There were also {cash} <:coin:632592319245451286> hidden inside!""")
                        scores[str(ctx.author.id)]["score"] += cash
                    if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                        scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                    else:
                        del scores[str(ctx.author.id)]["items"][has]
                else:
                    await ctx.send("You don't have that item...")
            else:
                await ctx.send("That item does not exist...")
        elif len(args) == 2:
            if args[0] in itemaliases["3"]:
                has = await hasitem(scores, ctx.author.id, 3)
                if not isinstance(has, bool):
                    if ctx.message.mentions:
                        member = ctx.message.mentions[0]
                    else:
                        member = ctx.guild.get_member_named(args[1])
                    if member:
                        for i in range(4):
                            await ctx.send(member.mention + ": get the fuck over here")
                        if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                            scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                        else:
                            del scores[str(ctx.author.id)]["items"][has]
                        amount = random.randint(10, 30)
                        await ctx.send(ctx.author.mention + f": {member.mention} was so startled they dropped {amount} <:coin:632592319245451286>")
                        scores[str(member.id)]["score"] -= amount
                        scores[str(ctx.author.id)]["score"] += amount
                    else:
                        await ctx.send("That member does not exist...")
                else:
                    await ctx.send("You don't have that item...")
            elif args[0] in itemaliases["4"]:
                has = await hasitem(scores, ctx.author.id, 4)
                if not isinstance(has, bool):
                    if ctx.message.mentions:
                        member = ctx.message.mentions[0]
                    else:
                        member = ctx.guild.get_member_named(args[1])
                    if member:
                        if scores[str(member.id)]["score"] >= 300:
                            amount = random.randint(40, 300)
                        elif scores[str(member.id)]["score"] < 50:
                            amount = 0
                        else:
                            amount = random.randint(40, scores[str(member.id)]["score"])
                        if amount:
                            scores[str(member.id)]["score"] -= amount
                            scores[str(ctx.author.id)]["score"] += amount
                            await ctx.send(ctx.author.mention + f": You robbed {member.mention}, you managed to get away with `{amount}` points!")
                            if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                                scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                            else:
                                del scores[str(ctx.author.id)]["items"][has]
                        else:
                            await ctx.send(ctx.author.mention + f": You cant rob {member.mention}! They're way too poor, thats pathetic... *shakes head disapprovingly*")
                    else:
                        await ctx.send("That member does not exist...")
            elif args[0] in itemaliases["7"]:
                has = await hasitem(scores, ctx.author.id, 7)
                if not isinstance(has, bool):
                    if ctx.message.mentions:
                        member = ctx.message.mentions[0]
                    else:
                        member = ctx.guild.get_member_named(args[1])
                    if member:
                        if scores[str(member.id)]["score"] >= 500:
                            amount = random.randint(0, 500)
                        elif scores[str(member.id)]["score"] < 0:
                            amount = random.randint(0, scores[str(member.id)]["score"] * -1) * -1
                        elif scores[str(member.id)]["score"] < 500:
                            amount = random.randint(0, scores[str(member.id)]["score"])
                        scores[str(member.id)]["score"] -= amount
                        scores[str(ctx.author.id)]["score"] += int(amount / 2)
                        await ctx.send(ctx.author.mention + f": You yeeted a nuke at {member.mention}, you stole `{amount}` points, but half of them were destroyed!")
                        if scores[str(ctx.author.id)]["items"][has]["count"] > 1:
                            scores[str(ctx.author.id)]["items"][has]["count"] -= 1
                        else:
                            del scores[str(ctx.author.id)]["items"][has]
                    else:
                        await ctx.send("That member does not exist...")
                else:
                    await ctx.send("You don't have that item...")
            else:
                await ctx.send("That item does not exist...")
        else:
            await ctx.send("Too many arguments.")
    else:
        await ctx.send("Please specify an item.")

@use.error
async def use_error(ctx, error):
    await ctx.send("Internal error: " + str(error))

@client.command(aliases=["xp"])
async def level(ctx, *args):
    """You probably won't get any higher than 2 or 3 tbh"""
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
async def shop(ctx, buythis=None):
    """Yo whattup come buy some stuffs"""
    if buythis:
        buythisid = 0
        for item in itemaliases:
            if item in shopcosts and buythis in itemaliases[item]:
                buythisid = int(item)
                break
        if buythisid:
            if scores[str(ctx.author.id)]["score"] >= shopcosts[str(buythisid)]:
                await ctx.send(f"""{ctx.author.mention}: you bought 1 {itemindex[str(buythisid)]["emoji"]} {itemindex[str(buythisid)]["displayname"]}""")
                scores[str(ctx.author.id)]["score"] -= shopcosts[str(buythisid)]
                await giveitem(ctx.author, itemindex[str(buythisid)], 1)
            else:
                await ctx.send("U ain't got da cash m8")
        else:
            await ctx.send("I don't sell that")
    else:
        embed = discord.Embed(title="For sale:", colour=discord.Colour(0x70a231))
        embed.set_author(name="yo whattup come buy some stuffs", icon_url=client.user.avatar_url)
        for item in shopcosts:
            embed.add_field(name=f"""**{itemindex[item]["emoji"]} {itemindex[item]["displayname"]}** - {shopcosts[item]} Points""", value=itemdescriptions[item], inline=False)
        await ctx.send(embed=embed)

@client.command()
async def helpiminfuckingdebt(ctx):
    if scores[str(ctx.author.id)]["score"] < 0:
        await ctx.send("ur in some deep shit my dude, lemme help u out")
        scores[str(ctx.author.id)]["score"] = 0
    else:
        await ctx.send("no ur not")

if channelid:
    client.loop.create_task(background())
client.loop.create_task(background3())
client.run(token)
