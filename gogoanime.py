import os
import json
import re
from urllib.parse import urljoin

import requests

import config
import utils
import outputs


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
    try:
        link = json.loads(r.text)['source_bk'][0]['file']
    except (IndexError, KeyError):
        outputs.error_info('Unexpected error while obtaining stream url')
        raise SystemExit
    _, ext = os.path.splitext(link)
    if ext == '.m3u8':
        link = utils.get_m3u8_stream(link)
    return link, ext


def get_episodes_range(anime_url):
    soup = utils.get_soup(anime_url)
    if not soup:
        return []
    rngs_obj = soup.find_all('a', ep_end=True, ep_start=True)
    total_rng = []
    for r in rngs_obj:
        rng = r.text
        rngs = rng.split('-')
        if rngs[0] == '0' and len(rngs) == 2:
            rngs[0] = '1'
        total_rng.append('-'.join(rngs))
    text = ','.join(total_rng)
    parsed_rng = utils.compress_range(utils.extract_range(text))
    return parsed_rng


def home_page():
    soup = utils.get_soup(config.gogoanime_url)
    div = soup.find('div', {'class': 'last_episodes'})
    eps = []
    for li in div.find_all('li'):
        try:
            link = li.find('a')['href']
            eps.append(parse_gogo_url(link))
        except SystemExit:
            continue
    return eps


def parse_gogo_url(url):
    whole_name = url.split('/')[-1]
    match = re.match(r'(.+)-episode-([0-9]+)', whole_name)
    if match:
        anime_name = match.group(1)
        episode = match.group(2)
    else:
        outputs.error_info("URL couldn't be parsed.")
        raise SystemExit
    return anime_name, episode


def verify_anime_exists(anime_name, verbose=False):
    if utils.read_log(anime_name) is not None:
        if verbose:
            outputs.normal_info(anime_name, 'LOG', reverse=True)
        return True
    elif anime_name in utils.read_cache(complete=True):
        if verbose:
            outputs.normal_info(anime_name, 'CACHE', reverse=True)
        return True
    elif utils.get_anime_path(anime_name, check=True)[0]:
        if verbose:
            outputs.normal_info(anime_name, 'LOCAL', reverse=True)
        return True
    elif utils.get_soup(get_anime_url(anime_name)) is not None:
        if verbose:
            outputs.normal_info(anime_name, 'SITE', reverse=True)
        return True
    else:
        return False
