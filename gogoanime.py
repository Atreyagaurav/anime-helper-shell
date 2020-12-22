import json
import re
from urllib.parse import urljoin

import requests

import config
import utils


def get_anime_url(anime_name):
    return urljoin(
        config.gogoanime_url,
        config.anime_t.substitute(anime=anime_name.lower().replace(' ', '-')))


def get_episode_url(anime_name, episode):
    return urljoin(
        config.gogoanime_url,
        config.episode_t.substitute(anime=anime_name.lower().replace(' ', '-'),
                                    ep=episode))


def process_anime_name(name):
    name = name.lower().replace(' ', '-')
    name = re.sub(r'\(|\)|:', '', name)
    return name


def get_direct_video_url(gogo_url):
    soup = utils.get_soup(gogo_url)
    php_l = soup.find('iframe')['src']
    ajx_l = config.ajax_t.substitute(q=php_l.split('?')[1])
    r = requests.get(ajx_l)
    link = json.loads(r.text)['source_bk'][0]['file']
    ftype = link.split('.')[-1]
    return link, ftype


def get_episodes_range(anime_url):
    soup = utils.get_soup(anime_url)
    if not soup:
        return []
    rngs_obj = soup.find_all('a', ep_end=True, ep_start=True)
    total_rng = []
    for r in rngs_obj:
        rng = r.text
        rngs = rng.split('-')
        if rngs[0] == '0':
            rngs[0] = '1'
        total_rng.append('-'.join(rngs))
    text = ','.join(total_rng)
    parsed_rng = utils.compress_range(utils.extract_range(text))
    return parsed_rng


def parse_gogo_url(url):
    whole_name = url.split('/')[-1]
    match = re.match(r'(.+)-episode-([0-9]+)', whole_name)
    if match:
        anime_name = match.group(1)
        episode = match.group(2)
    else:
        print("URL couldn't be parsed.")
        raise SystemExit
    return anime_name, episode


def verify_anime_exists(anime_name, verbose = False):
    url = get_anime_url(anime_name)
    soup = utils.get_soup(url)
    if utils.read_log(anime_name) is not None:
        if verbose:
            print(f'LOG::{anime_name}')
        return True
    elif anime_name in utils.read_cache(complete=True):
        if verbose:
            print(f'CACHE::{anime_name}')
        return True
    elif utils.get_soup(get_anime_url(anime_name)) is not None:
        if verbose:
            print(f'SITE::{anime_name}')
        return True
    else:
        return False
