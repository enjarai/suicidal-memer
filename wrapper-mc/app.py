#!/usr/bin/env python3
# Simple Minecraft Server Wrapper for snapshots and production releases.
# ======
# Finds the latest snapshot or production version, downloads and runs it.  Then
# every hour it checks for a new snapshot or production release.  If it finds one,
# it stops the server, downloads the update and restarts with the newest version.

import time, json, argparse, os, random
from ServerManager import ServerManager

# Global Settings

mc_server = 'fabric-server-launch.jar'  # server file name
buycommand = ".buy"
scoreslocation = "../../discordbots/scores.json"

# Process command line arguments for memory settings
def process_args():
    global results
    parser = argparse.ArgumentParser(description="Simple Minecraft Server Wrapper")
    #parser.add_argument("-m", action='store', dest='memmin',
                        #help="Sets the minimum/initial memory usage for the Minecraft server in GB (ex: 1, 2, 3, 4)",
                        #type=int, default=1)
    #parser.add_argument("-x", action='store', dest='memmax',
                        #help="Sets the maximum memory usage for the Minecraft server in GB (ex: 1, 2, 3, 4)", type=int,
                        #default=1)
    #parser.add_argument("-p", action='store', dest='path',
                        #help="Set the local path where you want the server downloaded and ran, default is local directory",
                        #type=str, default='')
    #parser.add_argument("-g", action='store_true', dest='gui', help="Utilize the Minecraft server GUI, default is off")
    parser.add_argument("-m", action='store', dest='memmin', help="Set the minimum memory for Minecraft in GB (ex: 1, 2, 3, 4).  Default is 3.", type=int, default=3)
    parser.add_argument("-x", action='store', dest='memmax', help="Set the maximum memory for Minecraft in GB (ex: 1, 2, 3, 4).  Default is 3.", type=int, default=3)
    parser.add_argument("-p", action='store', dest='path', help="Specify another directory to run the server.", type=str, default='')
    parser.add_argument("-g", action='store_true', dest='gui', help="   Utilize the Minecraft server GUI.  Default is off")
    parser.add_argument("-s", action='store_true', dest='stable', help="Use stable release of Minecraft instead of development snapshots.")
    results = parser.parse_args()
    if results.path != '': results.path = os.path.join(results.path, '')  # Path handling to include the trailing slash
    return

# Supervisor program
def main():
    process_args()
    server = ServerManager(results.path, mc_server, results.memmin, results.memmax, results.gui)
    print('*' * 40)
    print('* Simple Minecraft Server Wrapper')
    print('*' * 40)
    #latest_ver = str(get_version())
    #if current_ver != latest_ver:
    #    download_server(latest_ver)
    #    current_ver = latest_ver
    if not server.online:
        server.start()
        time.sleep(1)
        while server.online:
            line = server.process.stdout.readline().decode("utf-8")
            if not line: break
            print(line)

            line2 = line.split(">")
            if "[Server thread/INFO]" in line2[0] and "<" in line2[0]:
                sender = line2[0].split("<")[1]
                line2 = "".join(line2[1:])[1:]
                if line2.startswith(buycommand):
                    with open(scoreslocation) as f:
                        scores = json.load(f)
                    with open('shop.json') as f:
                        shop = json.load(f)
                    id = 0
                    for key, value in scores.items():
                        if "mcacc" in value and value["mcacc"].lower() == sender.lower():
                            id = int(key)
                            break
                    if id:
                        line3 = line2[len(buycommand) + 1:].rstrip()
                        if line3:
                            if line3 in shop:
                                if scores[str(id)]["score"] >= shop[line3]["cost"]:
                                    scores[str(id)]["score"] -= shop[line3]["cost"]
                                    randomstring = str(random.randint(1000000, 9999999))
                                    server.message(shop[line3]["command"].format(sender=sender, randomstring=randomstring), True)
                                    server.message(f"msg {sender} you bought: {line3}", True)
                                    with open(scoreslocation, 'w') as f:
                                        json.dump(scores, f, indent=4)
                                else:
                                    server.message(f"msg {sender} you do not have enough points", True)
                            else:
                                server.message(f"msg {sender} that is not in the shop", True)
                        else:
                            server.message(f"""msg {sender} you have {scores[str(id)]["score"]} points""", True)
                            for name, item in shop.items():
                                server.message(f"""msg {sender} {name}: {item["name"]} | {item["cost"]}""", True)
                    else:
                        server.message(f"msg {sender} please link your account via discord with the '-mclink <username>' command", True)
                

            if server.crash_check():
                del server
                main()
            #server.message("test")
            #server.message("give @a bone 1", True)


# Start when run.
if __name__ == '__main__':
    main()
