import os
import re
import math
import time
import datetime as dt
import subprocess

import pycurl
import m3u8
import requests

from bs4 import BeautifulSoup

import config
import outputs


class Log:
    def __init__(self, logline, eps=None):
        if not logline:
            self.anime = ''
            self.eps = ''
            self.last_updated = None
            return
        data = logline.split()
        self.anime = data[0]
        if eps:
            self.eps = eps
            self.last_updated = dt.datetime.now()
        else:
            self.eps = data[1]
            if len(data) > 2:
                self.last_updated = dt.datetime.fromtimestamp(int(data[2]))
            else:
                self.last_updated = None

    @property
    def last_updated_fmt(self):
        if self.last_updated:
            return self.last_updated.strftime("%Y-%m-%d %H:%M %A")
        return ''

    def add(self, eps):
        self.eps = compress_range(extract_range(f'{self.eps},{eps}'))

        self.last_updated = dt.datetime.now()
        return self

    def edit(self, eps):
        self.eps = eps
        self.last_updated = dt.datetime.now()
        return self

    def __str__(self):
        rep = f'{self.anime} {self.eps}'
        if self.last_updated:
            rep += f' {int(self.last_updated.timestamp())}'
        return rep

    @property
    def _eps(self):
        if len(self.eps) > 10:
            data = re.split(f',|-', self.eps)
            return f'{data[0]}...{data[-1]}'
        else:
            return self.eps
    
    def show(self):
        rep = f'{self._eps}\t\t{self.anime} ({self.last_updated_fmt})'
        return rep


def get_soup(url):
    r = requests.get(url, headers=config.req_headers)
    if r.status_code == 404:
        return None
    return BeautifulSoup(r.text, 'html.parser')


def download_file(url, filepath, replace=False):
    if os.path.exists(filepath) and not replace:
        outputs.warning_info('File already downloaded, skipping.')
        return
    part_file = f'{filepath}.part'

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.NOPROGRESS, 0)

    curl_header = [f'{k}: {v}' for k, v in config.down_headers.items()]

    if os.path.exists(part_file) and not replace:
        outputs.normal_info('Previously Downloaded part found.')
        wmode = 'ab'
        curl_header.append(
            config.resume_t.substitute(size=os.path.getsize(part_file)))
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
        outputs.error_info(f"Download Failed {e}")
        raise SystemExit

    os.rename(part_file, filepath)


def download_m3u8(url, filepath, replace=False):
    if os.path.exists(filepath) and not replace:
        outputs.warning_info('File already downloaded, skipping.')
        return
    part_file = f'{filepath}.part'
    if os.path.exists(part_file) and not replace:
        outputs.normal_info('Previously Downloaded part found.')
        # TODO: resume download
    media = m3u8.load(url)
    total = len(media.segments)
    with open(part_file, 'wb') as writer:
        c = pycurl.Curl()
        curl_header = [f'{k}: {v}' for k, v in config.down_headers.items()]
        c.setopt(pycurl.HTTPHEADER, curl_header)
        c.setopt(pycurl.WRITEDATA, writer)
        try:
            for i, f in enumerate(media.segments):
                uri = f.absolute_uri
                c.setopt(pycurl.URL, uri)
                c.perform()
                outputs.normal_info('\rDownloaded :',
                                    '#' * (((i + 1) * 40) // total),
                                    f'{(i+1)*100//total}% ({i+1} of {total})',
                                    end="")
            c.close()
        except (KeyboardInterrupt, pycurl.error) as e:
            c.close()
            raise SystemExit(f"Download Failed {e}")
    outputs.normal_info()
    os.rename(part_file, filepath)


def get_m3u8_stream(m3u8_url):
    media = m3u8.load(m3u8_url)
    if media.data['is_variant']:
        flag = False
        for p in media.playlists:
            if (p.stream_info.resolution[1] <=
                    config.QUALITY_PREFERENCE) or (not flag):
                m3u8_url = p.absolute_uri
                flag = True
    return m3u8_url


def read_cache(num=1, complete=False):
    if not os.path.exists(config.cachefile):
        return list() if complete else None
    else:
        with open(config.cachefile, 'r') as r:
            lines = r.readlines()
        if complete:
            return list(map(lambda l: l.strip(), lines))
        else:
            try:
                return lines[num - 1].strip()
            except IndexError:
                outputs.error_info("The choice number is too large.")
                outputs.prompt_val("Total items in cache", len(lines), 'error')
                raise SystemExit


def write_cache(anime, append=False):
    with open(config.cachefile, 'a' if append else 'w') as w:
        w.write(f'{anime}\n')


def clear_cache():
    if os.path.exists(config.cachefile):
        os.remove(config.cachefile)


def read_log(anime_name=None,
             number=math.inf,
             pattern=re.compile(r'.*'),
             logfile=config.logfile):
    if not os.path.exists(logfile):
        log = dict()
    else:
        log = {
            line[0]: " ".join(line)
            for i, line in enumerate(li.strip().split()
                                     for li in open(logfile, 'r')
                                     if pattern.match(li.split()[0]))
            if i < number
        }
    if not anime_name:
        return log
    return log.get(anime_name)


def write_log(anime_name, episodes, append=True, logfile=config.logfile):
    log = read_log(logfile=logfile)
    if anime_name in log and append:
        log[anime_name] = str(Log(log[anime_name]).add(episodes))
    else:
        log[anime_name] = str(Log(anime_name, episodes))
    with open(logfile, 'w') as w:
        w.writelines((f'{v}\n' for v in log.values()))


def remove_anime_from_log(anime_name, logfile=config.logfile):
    anime_list = read_log(logfile=logfile)
    if anime_name in anime_list:
        anime_list.pop(anime_name)
    else:
        return
    logs = sorted(
        map(Log, anime_list.values()),
        key=lambda l: ((int(l.last_updated.timestamp()) if l.last_updated else 0) -  # - since it's reverse
                  (ord(l.anime[0])-ord('a'))/26),
        reverse=True)
    with open(logfile, "w") as w:
        for log in logs:
            w.write(f"{str(log)}\n")


def update_tracklist(anime_name, episodes, append=True):
    log = read_log(anime_name, logfile=config.ongoingfile)
    if log:
        write_log(anime_name,
                  episodes,
                  append=append,
                  logfile=config.ongoingfile)

def update_watchlater(anime_name, episode=None):
    log = read_log(anime_name, logfile=config.watchlaterfile)
    if log:
        eps = set(extract_range(Log(log).eps)).difference(
            set([episode])
        )
        if not eps:
            remove_anime_from_log(anime_name, logfile=config.watchlaterfile)
        else:
            write_log(anime_name,
                      compress_range(eps),
                      append=True,
                      logfile=config.watchlaterfile)


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
    if range_str is None or range_str.strip() == '':
        return
    ranges = range_str.split(',')
    try:
        for r in ranges:
            if r.strip() == '':
                continue
            if '-' in r:
                rng = r.split('-')
                if len(rng) > 2:
                    outputs.prompt_val('Incorrect formatting', r, 'error')
                    raise SystemExit
                yield from range(int(rng[0]), int(rng[1]) + 1)
            else:
                yield int(r)
    except ValueError as e:
        outputs.error_info('Incorrect formatting: use integers for episodes')
        outputs.error_tag(e)
        raise SystemExit


def recursive_getattr(obj, attr=None):
    if attr is None or '.' not in attr:
        return dir(obj)
    else:
        attrs = attr.split('.', 1)
        try:
            return map(lambda s: f'{attrs[0]}.{s}',
                       recursive_getattr(getattr(obj, attrs[0]), attrs[1]))
        except AttributeError:
            return []


def get_anime_path(anime_name, *, make=False, check=False):
    """returns tuple (anime path, existed before)
    """
    anime_dir = os.path.join(config.anime_dir, anime_name)
    if not os.path.isdir(anime_dir):
        if make:
            os.mkdir(anime_dir)
            return anime_dir, False
        elif check:
            return None, False
        else:
            return anime_dir, False
    return anime_dir, True


def get_local_episodes(pattrn=r'^[0-9a-z-]+$'):
    animes = dict()
    for folder in os.listdir(config.anime_dir):
        if not os.path.isdir(os.path.join(config.anime_dir, folder)) or \
           not re.match(pattrn, folder):
            continue
        animes[folder] = ''
        for f in os.listdir(os.path.join(config.anime_dir, folder)):
            m = re.match(r'^ep([0-9]+)\.[a-z0-9]+$', f)
            if m:
                animes[folder] += f',{m.group(1)}'
    return animes


def get_episode_path(anime_name,
                     episode,
                     *,
                     ext='.mp4',
                     make=False,
                     check=False):
    anime_dir, existed = get_anime_path(anime_name, make=make, check=check)
    if anime_dir is None:
        return None
    ep_path = os.path.join(anime_dir, f'ep{episode:02d}{ext}')
    if check and not os.path.isfile(ep_path):
        return None
    return ep_path


def completion_list(iterator):
    return [f'{s} ' for s in iterator]
