#!/usr/bin/env python
import json
import os
import re
import sys
from string import Template
from urllib.parse import urljoin

import subprocess
import time
import pycurl
import m3u8
import requests
import html2text
from bs4 import BeautifulSoup

QUALITY_PREFERENCE = 720

gogoanime_url = 'https://gogoanime.so'

ajax_t = Template('https://gogo-stream.com/ajax.php?${q}')

mpv_command = [
    'mpv', '--geometry=300-0-20', '--on-all-workspaces', '--no-config'
]

anime_dir = os.path.abspath('/home/gaurav/anime')

cachefile = os.path.join(anime_dir, ".cachefile")
logfile = os.path.join(anime_dir, ".anime_history")


episode_t = Template("${anime}-episode-${ep}")
anime_t = Template("category/${anime}")
resume_t = Template("Range: bytes=${size}-")
search_t = Template("https://gogoanime.so//search.html?keyword=${name}")
search_page_t = Template(
    "https://gogoanime.so//search.html?keyword=${name}&page=${page}")

req_headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Upgrade-Insecure-Requests": "1"
}

down_headers = {
    "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64; rv:82.0) Gecko/20100101 Firefox/82.0",
    "Accept":
    "video/webm,video/ogg,video/*;q=0.9,application/ogg;q=0.7,audio/*;q=0.6,*/*;q=0.5",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_anime_url(anime_name):
    return urljoin(
        gogoanime_url,
        anime_t.substitute(anime=anime_name.lower().replace(' ', '-')))


def get_episode_url(anime_name, episode):
    return urljoin(
        gogoanime_url,
        episode_t.substitute(anime=anime_name.lower().replace(' ', '-'),
                             ep=episode))


def process_anime_name(name):
    name = name.lower().replace(' ', '-')
    name = re.sub(r'\(|\)|:', '', name)
    return name


def download_file(url, filepath, replace=False):
    if os.path.exists(filepath) and replace == False:
        print('File already downloaded, skipping.')
        return
    part_file = f'{filepath}.part'

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.NOPROGRESS, 0)

    curl_header = [f'{k}: {v}' for k, v in down_headers.items()]

    if os.path.exists(part_file) and replace == False:
        print('Previously Downloaded part found.')
        wmode = 'ab'
        curl_header.append(
            resume_t.substitute(size=os.path.getsize(part_file)))
    else:
        wmode = 'wb'
    c.setopt(pycurl.HTTPHEADER, curl_header)
    try:
        with open(part_file, wmode) as writer:
            c.setopt(pycurl.WRITEDATA, writer)
            c.perform()
            c.close()
    except (KeyboardInterrupt, pycurl.error) as e:
        c.close()
        raise SystemExit(f"Download Failed {e}")

    os.rename(part_file, filepath)


def download_m3u8(url, filepath, replace=False):
    if os.path.exists(filepath) and replace == False:
        print('File already downloaded, skipping.')
        return
    part_file = f'{filepath}.part'
    media = m3u8.load(url)
    total = len(media.segments)
    with open(part_file, 'wb') as writer:
        c = pycurl.Curl()
        curl_header = [f'{k}: {v}' for k, v in down_headers.items()]
        c.setopt(pycurl.HTTPHEADER, curl_header)
        c.setopt(pycurl.WRITEDATA, writer)
        try:
            for i,f in enumerate(media.segments):
                uri = f.absolute_uri
                c.setopt(pycurl.URL, uri)
                c.perform()
                print('\rDownloaded :',f'{(i+1)*100//total}% ({i+1} of {total})',end="")
            c.close()
        except (KeyboardInterrupt, pycurl.error) as e:
            c.close()
            raise SystemExit(f"Download Failed {e}")
    print()
    os.rename(part_file, filepath)


def get_soup(url):
    r = requests.get(url, headers=req_headers)
    if r.status_code == 404:
        return None
    return BeautifulSoup(r.text, 'html.parser')


def get_direct_video_url(gogo_url):
    soup = get_soup(gogo_url)
    php_l = soup.find('iframe')['src']
    ajx_l = ajax_t.substitute(q=php_l.split('?')[1])
    r = requests.get(ajx_l)
    link = json.loads(r.text)['source_bk'][0]['file']
    ftype = link.split('.')[-1]
    return link, ftype


def get_m3u8_stream(m3u8_url):
    media = m3u8.load(m3u8_url)
    if media.data['is_variant']:
        first = False
        for p in media.playlists:
            if not first:
                m3u8_url = p.absolute_uri
            elif p.stream_info.resolution[1] > QUALITY_PREFERENCE:
                break
            else:
                m3u8_url = p.absolute_uri
    return m3u8_url


def read_cache(num=1, complete=False):
    if not os.path.exists(cachefile):
        return list() if complete else None
    else:
        with open(cachefile, 'r') as r:
            lines = r.readlines()
        if complete:
            return list(map(lambda l:l.strip(),lines))
        else:
            return lines[num-1].strip()


def write_cache(anime, append=False):
    with open(cachefile, 'a' if append else 'w') as w:
        w.write(f'{anime}\n')


def clear_cache():
    if os.path.exists(cachefile):
        os.remove(cachefile)


def read_log(anime_name=None):
    if not os.path.exists(logfile):
        log = dict()
    else:
        with open(logfile, 'r') as r:
            # what happens when file is used as iterator, need to close?
            log = {l[0]: l[1] for l in (li.strip().split() for li in r)}
    if anime_name == None:
        return log
    return log.get(anime_name)


def write_log(anime_name, episodes):
    log = read_log()
    if anime_name in log:
        log[anime_name] = compress_range(
            extract_range(f'{log[anime_name]},{episodes}'))
    else:
        log[anime_name] = episodes
    with open(logfile, 'w') as w:
        w.writelines((f'{k} {v}\n' for k, v in log.items()))


def anime_log(args):
    print(f'Watched:\tAnime Name:')
    logs = read_log().items()
    if len(args) == 1:
        logs = filter(lambda kv: re.match(args[0], kv[0]), logs)
    for k, v in logs:
        print(f'{v}\t\t{k}')


def play_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        url = get_episode_url(name, e)
        stream_from_url(url, name, e)


def update_log(args):
    anime_name, episodes = read_args(args)
    write_log(anime_name, compress_range(episodes))


def continue_play(args):
    name, episodes = read_args(args)
    watched = read_log().get(name)
    print(f'Watched: {watched}')
    if watched == None:
        last = 0
    else:
        last = int(watched.split('-')[-1])
    play_anime([name, compress_range(filter(lambda e: e > last, episodes))])


def download_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        url = get_episode_url(name, e)
        download_from_url(url, name, e)
        


def check_anime(args):
    name, episodes = read_args(args)
    unavail_eps = []
    for e in episodes:
        url = get_episode_url(name, e)
        print('Testing:', url)
        durl, ext = get_direct_video_url(url)
        if durl == None:
            raise SystemExit('Url for the file not found')
        if not os.path.exists(
                os.path.join(anime_dir, f'./{name}/ep{e:02d}.{ext}')):
            unavail_eps.append(e)
    if len(unavail_eps) == 0:
        print('All episodes in given range are locally available')
    else:
        print(f'Missing episodes: {compress_range(unavail_eps)}')


def get_episodes_range(anime_url):
    soup = get_soup(anime_url)
    if soup == None:
        return []
    rngs_obj = soup.find_all('a', ep_end=True, ep_start=True)
    total_rng = []
    for r in rngs_obj:
        rng = r.text
        rngs = rng.split('-')
        if rngs[0] == '0':
            rngs[0] = '1'
        total_rng.append('-'.join(rngs))
    return ','.join(total_rng)


def compress_range(range_list):
    range_list = sorted(range_list)
    if len(range_list) == 0:
        return ''
    rng_str = f'{range_list[0]}'
    prev = range_list[0]
    rng = False
    for r in range_list[1:]:
        if r == prev:
            continue
        if r == (prev + 1):
            if not rng:
                rng_str += '-'
            rng = True
        else:
            if rng:
                rng_str += f'{prev},{r}'
            else:
                rng_str += f',{r}'
            rng = False
        prev = r

    if rng:
        rng_str += f'{prev}'
    return rng_str


def extract_range(range_str):
    ranges = range_str.split(',')
    try:
        for r in ranges:
            if '-' in r:
                rng = r.split('-')
                if len(rng) > 2:
                    print(f'Incorrect formatting: {r}')
                    raise SystemExit
                yield from range(int(rng[0]), int(rng[1]) + 1)
            else:
                yield int(r)
    except ValueError as e:
        print(f'Incorrect formatting: use integers for episodes: \n{e}')
        raise SystemExit


def read_args(args, episodes=True):
    if len(args) == 0:
        name = read_cache()
    elif args[0].isnumeric():
        name = read_cache(int(args[0]))
        print(name)
    elif '/' in args[0]:
        name = args[0].strip('/').split('/')[-1]
    else:
        name = process_anime_name(args[0])
        if (not os.path.exists(os.path.join(anime_dir,
                                            f'./{name}'))) and get_soup(
                                                get_anime_url(name)) == None:
            print(
                f'Anime with name doesn\'t exist: {" ".join(name.split("-"))}')
            raise SystemExit

    if name == None:
        print('Numbers choice invalid, or invalid context.')
        raise SystemExit
    os.makedirs(os.path.join(anime_dir, f'./{name}'), exist_ok=True)

    if episodes == False:
        return name
    if len(args) <= 1:
        print('Episodes range not given defaulting to all')
        available_rng = get_episodes_range(get_anime_url(name))
        print(f'Available episodes: {available_rng}')
        episodes = extract_range(available_rng)
    elif len(args) == 2:
        episodes = extract_range(args[1])
    else:
        print('Too many arguments.\n')
        print(__doc__)
        raise SystemExit
    return name, episodes


def list_episodes(args):
    name, episodes = read_args(args)
    if len(sys.argv) == 4:
        eps = set(episodes)
        avl_eps = set(extract_range(get_episodes_range(get_anime_url(name))))
        res = eps.intersection(avl_eps)
        result = compress_range(res)
        print(f'Available episodes: {result}')
    print(f'Watched episodes: {read_log().get(name)}')
    write_cache(name)


def search_anime(args):
    name = " ".join(args)
    url = search_t.substitute(name=name)
    soup = get_soup(url)
    plist = soup.find('ul', {'class': 'pagination-list'})
    clear_cache()

    def search_results(s):
        all_res = s.find('ul', {'class': 'items'})
        for l in all_res.find_all('li'):
            an = l.p.a['href'].split('/')[-1]
            write_cache(an, append=True)
            print(an, end='  \t')
            print(l.p.a.text)

    search_results(soup)
    if plist:
        for l in plist.find_all('li', {'class': None}):
            url = search_page_t.substitute(name=name, page=l.a.text)
            soup = get_soup(url)
            search_results(soup)


def anime_info(args):
    name = read_args(args, episodes=False)
    soup = get_soup(get_anime_url(name))
    info = soup.find('div', {'class': 'anime_info_body'})
    h = html2text.HTML2Text()
    h.ignore_links = True
    for t in info.find_all('p', {'class': 'type'}):
        print(h.handle(t.decode_contents()), end="")


def download_from_url(gogo_url, anime_name = None, episode = None):
    if anime_name == None or episode == None:
        anime_name, episode = parse_gogo_url(url)
    print('Downloading:', gogo_url)
    durl, ext = get_direct_video_url(gogo_url)
    if durl == None:
        raise SystemExit('Url for the file not found')
    if ext == 'm3u8':
        print("m3u8 file found")
        m3u8_url = get_m3u8_stream(durl)
        download_m3u8(m3u8_url,os.path.join(anime_dir,
                                     f'./{anime_name}/ep{episode:02d}.{ext}'))
    else:
        download_file(durl, os.path.join(anime_dir,
                                     f'./{anime_name}/ep{episode:02d}.{ext}'))

def parse_gogo_url(url):
    whole_name = url.split('/')[-1]
    match = re.match(r'(.+)-episode-([0-9]+)',whole_name)
    if match:
        anime_name = match.group(1)
        episode = match.group(2)
        download_anime([anime_name,episode])
    else:
        print("URL couldn't be parsed.")
        raise SystemExit
    return anime_name, episode


def stream_from_url(url, anime_name = None, episode = None):
    if anime_name == None or episode == None:
        anime_name, episode = parse_gogo_url(url)
    print('Getting Streaming Link:', url)
    durl, ext = get_direct_video_url(url)
    if durl == None:
        raise SystemExit('Url for the file not found')
    if ext == 'm3u8':
        print("m3u8 file found")
        durl = get_m3u8_stream(durl)
    print(f'Stream link: {durl}')
    if input('Start mpv?<Y/n>:')=='n':
        raise SystemExit
    t1 = time.time()
    subprocess.call(" ".join(mpv_command + [durl]), shell=True)
    if (time.time() - t1) > (
            5 * 60
    ):  # 5 minutes watchtime at least, otherwise consider it unwatched
        write_log(anime_name, episode)
        write_cache(anime_name)
