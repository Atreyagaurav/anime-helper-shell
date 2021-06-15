import os
from string import Template

QUALITY_PREFERENCE = 720

gogoanime_url = 'https://gogoanime.ai'

ajax_t = Template('https://gogo-stream.com/ajax.php?${q}')

ask_before_open = False
geometry = '300-0-20'
fullscreen = True

ext_player_command = ''
# Should be set from
# compile_ext_player_command function


def compile_ext_player_command():
    global ext_player_command
    com = ['mpv']
    com += [f'--geometry={geometry}']
    com += ['--on-all-workspaces']
    if fullscreen:
        com += ['--fs']
    com += ['--no-config']
    ext_player_command = com
    return com


compile_ext_player_command()

anime_dir = os.path.expanduser('~/anime')
os.makedirs(anime_dir, exist_ok=True)

cachefile = os.path.join(anime_dir, ".cachefile")
historyfile = os.path.join(anime_dir, ".shell_history")
logfile = os.path.join(anime_dir, ".anime_history")
ongoingfile = os.path.join(anime_dir, ".ongoing")
watchlaterfile = os.path.join(anime_dir, ".watch_later")


episode_t = Template("${anime}-episode-${ep}")
anime_t = Template("category/${anime}")
resume_t = Template("Range: bytes=${size}-")
search_t = Template(gogoanime_url + "//search.html?keyword=${name}")
search_page_t = Template(
    gogoanime_url + "//search.html?keyword=${name}&page=${page}")

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
}
