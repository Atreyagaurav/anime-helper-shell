import os


anime_dir = os.path.expanduser('~/anime')
os.makedirs(anime_dir, exist_ok=True)

cachefile = os.path.join(anime_dir, ".cachefile")
historyfile = os.path.join(anime_dir, ".shell_history")
logfile = os.path.join(anime_dir, ".anime_history")
ongoingfile = os.path.join(anime_dir, ".ongoing")
watchlaterfile = os.path.join(anime_dir, ".watch_later")

configfile = os.path.join(anime_dir, "shell.conf")
if not os.path.exists(configfile):
    print(f"Config file doesn't exist in {configfile}")
    exit(0)


project_dir = os.path.abspath(os.path.dirname(__file__))


def is_config_line(line):
    line = line.strip()
    if not line:
        return False
    if line[0] == '#':
        return False
    return True


with open(configfile, "r") as r:
    lines = filter(is_config_line, r)
    configs = dict()
    for line in lines:
        key, val = line.split("=", 1)
        configs[key.strip()] = val.strip(' "\n')


ext_player = configs["ext_player"]
ext_player_flags = configs["ext_player_flags"]
anime_source = configs["anime_source"]
video_quality = int(configs["video_quality"])

ext_player_confirm = configs["ext_player_confirm"].lower() in [
    'true', 'yes', 'on']

ext_player_fullscreen = configs["ext_player_fullscreen"].lower() in [
    'true', 'yes', 'on']


req_headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:84.0) Gecko/2010010 Firefox/84.0",
    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Upgrade-Insecure-Requests": "1"
}

down_headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:82.0) Gecko/20100102 Firefox/82.0",
    "Accept":
    "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
    "Accept-Language": "en-US,en;q=0.5",
    "referer":"https://gogoanime.gg/"
}
