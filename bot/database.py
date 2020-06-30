import sqlite3
import datetime

class Database(object):
    def __init__(self, filename: str):
        self.connector = sqlite3.connect(filename)

        self.connector.execute("""CREATE TABLE IF NOT EXISTS main.users (
            id INTEGER PRIMARY KEY UNIQUE NOT NULL,
            balance INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 0,
            xp INTEGER NOT NULL DEFAULT 0,
            lastsalary TEXT NOT NULL DEFAULT ""
        );""") 
        # ALTER TABLE main.users ADD lastsalary TEXT NOT NULL DEFAULT "";
        # INSERT INTO main.users (id, balance, level, xp) SELECT id, balance, level, xp FROM _users_old

        self.connector.commit()

    def close(self):
        self.connector.close()

    def setup_user(self, userid: int):
        self.connector.execute("INSERT OR IGNORE INTO main.users (id) VALUES (?);", (str(userid),))
        self.connector.execute(f"""CREATE TABLE IF NOT EXISTS main.inv_{userid} (
            id INTEGER PRIMARY KEY UNIQUE NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            CHECK (amount >= 0)
        );""")
        self.connector.execute(f"""CREATE TABLE IF NOT EXISTS main.eff_{userid} (
            name TEXT PRIMARY KEY UNIQUE NOT NULL,
            amount INTEGER NOT NULL DEFAULT 0,
            CHECK (amount >= 0)
        );""")
        self.connector.execute(f"""CREATE TABLE IF NOT EXISTS main.hist_{userid} (
            id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
            time TEXT NOT NULL,
            type TEXT NOT NULL,
            affected INTEGER NOT NULL DEFAULT 0,
            amount INTEGER NOT NULL DEFAULT 0,
            handled INTEGER NOT NULL DEFAULT 0
        );""")

        self.connector.commit()

    def all_users(self):
        c = self.connector.execute(f"SELECT id FROM main.users;")
        c = c.fetchall()
        return [x[0] for x in c]

    def get(self, column: str, userid: int):
        c = self.connector.execute(f"SELECT {column} FROM main.users WHERE id = ?;", (str(userid),))
        return c.fetchone()[0]

    def update(self, column: str, userid: int, amount: int):
        self.connector.execute(f"UPDATE main.users SET {column} = {column} + ? WHERE id = ?;", (str(amount), str(userid)))

        self.connector.commit()
        return True

    def set(self, column: str, userid: int, to: int):
        self.connector.execute(f"UPDATE main.users SET {column} = ? WHERE id = ?;", (str(to), str(userid)))

        self.connector.commit()
        return True

    def get_bal(self, *args, **kwargs):
        return self.get("balance", *args, **kwargs)

    def update_bal(self, *args, **kwargs):
        return self.update("balance", *args, **kwargs)

    def get_inv(self, userid: int):
        c = self.connector.execute(f"SELECT * FROM main.inv_{userid}")
        return c.fetchall()

    def give_item(self, userid: int, itemid: int, amount=1):
        self.connector.execute(f"INSERT OR IGNORE INTO main.inv_{userid} (id) VALUES (?);", (str(itemid),))
        self.connector.execute(f"UPDATE main.inv_{userid} SET amount = amount + ? WHERE id = ?;", (str(amount), str(itemid)))

        self.connector.commit()
        return True

    def rem_item(self, userid: int, itemid: int, amount=1):
        try:
            self.connector.execute(f"UPDATE main.inv_{userid} SET amount = amount - ? WHERE id = ?;", (str(amount), str(itemid)))
        except sqlite3.IntegrityError:
            return False

        self.connector.execute(f"DELETE FROM main.inv_{userid} WHERE amount = 0;")

        self.connector.commit()
        return True

    def has_item(self, userid: int, itemid: int, amount=1):
        c = self.connector.execute(f"SELECT EXISTS(SELECT id FROM main.inv_{userid} WHERE id = ? AND amount >= ?);", (itemid, amount))
        return c.fetchone()[0]

    def get_eff(self, userid: int):
        c = self.connector.execute(f"SELECT * FROM main.eff_{userid}")
        d = {}
        for k, i in c.fetchall():
            d[k] = i
        return d

    def give_eff(self, userid: int, name: str, amount=1):
        self.connector.execute(f"INSERT OR IGNORE INTO main.eff_{userid} (name) VALUES (?);", (name,))
        self.connector.execute(f"UPDATE main.eff_{userid} SET amount = amount + ? WHERE name = ?;", (str(amount), str(name)))

        self.connector.commit()
        return True

    def rem_eff(self, userid: int, name: str, amount=1):
        try:
            self.connector.execute(f"UPDATE main.eff_{userid} SET amount = amount - ? WHERE name = ?;", (str(amount), str(name)))
        except sqlite3.IntegrityError:
            return False
            
        self.connector.execute(f"DELETE FROM main.eff_{userid} WHERE amount = 0;")

        self.connector.commit()
        return True

    def has_eff(self, userid: int, name: str, amount=1):
        c = self.connector.execute(f"SELECT EXISTS(SELECT name FROM main.inv_{userid} WHERE name = ? AND amount >= ?);", (name, str(amount)))
        return c.fetchone()[0]

    def log(self, userid: int, htype: str, affected=0, amount=0):
        now = datetime.datetime.now()
        nowstr = datetime.datetime.strftime(now, "%Y-%m-%dT%H:%M:%S")

        self.connector.execute(f"INSERT INTO main.hist_{userid} (time, type, affected, amount) VALUES (?, ?, ?, ?);", (nowstr, htype, str(affected), str(amount)))

        self.connector.commit()
        return True

    def latest_log(self, userid: int, htype: str, limit=None):
        if not limit:
            limit = datetime.datetime.now() - datetime.timedelta(hours=1)

        try:
            c = self.connector.execute(f"SELECT MAX(id), time, affected, amount FROM main.hist_{userid} WHERE type = ? AND handled = 0;", (htype,))
            entryid, time, affected, amount = c.fetchone()
            if not datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S") > limit:
                return None
        except TypeError:
            return None

        self.connector.execute(f"UPDATE main.hist_{userid} SET handled = 1 WHERE id = ?;", (str(entryid),))
        
        self.connector.commit()
        return affected, amount
