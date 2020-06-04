from database import Database
import json

with open("scores.json", "r") as f:
    scores = json.load(f)

db = Database("converted.db")

for userid, userdata in scores.items():
    db.setup_user(userid)
    db.update_bal(userid, userdata["score"])
    db.update("level", userid, userdata["level"])
    db.update("xp", userid, userdata["xp"])
    for item in userdata["items"]:
        db.give_item(userid, item["id"], item["count"])
    for name, value in userdata["effects"].items():
        db.give_eff(userid, name, value)