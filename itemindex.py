class Item(object):
    def __init__(self, itemid: int, name: str, use=None, emoji=":question:", aliases=[], description="#PLACEHOLDER", lootboxmax=0, lootboxweight=0, buy=0, sell=0, useargs="", genaliases=True):
        self.id = itemid
        self.use = use
        self.name = name
        self.emoji = emoji
        self.aliases = aliases
        self.description = description
        self.lootboxmax = lootboxmax
        self.lootboxweight = lootboxweight
        self.buy = buy
        self.sell = sell
        self.useargs = useargs

        if genaliases:
            lowername = name.lower()
            self.aliases.append(lowername.strip())
            for i in lowername.split():
                self.aliases.append(i)
            self.aliases = list(set(self.aliases))

    def __str__(self):
        return f"{self.emoji} {self.name}"

    def json(self):
        return {
            "displayname": self.name,
            "emoji": self.emoji,
            "id": self.id
        }

class ItemIndex(object):
    def __init__(self, name):
        self.name = name
        self.items = []
        self.lastid = 0

    def add(self, *args, **kwargs):
        itemid = self.lastid
        self.items.append(Item(itemid, *args, **kwargs))
        self.lastid += 1

    def get_by_alias(self, name):
        return next((item for item in self.items if name.lower() in item.aliases), None)

    def get_by_id(self, itemid):
        return next((item for item in self.items if itemid == item.id), None)