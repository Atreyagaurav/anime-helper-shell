import os
import re
import math
import pycurl
import m3u8
import requests
from bs4 import BeautifulSoup

import config
import outputs


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
            return lines[num - 1].strip()


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
            line[0]: " ".join(line[1:])
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
        log[anime_name] = compress_range(
            extract_range(f'{log[anime_name]},{episodes}'))
    else:
        log[anime_name] = episodes
    with open(logfile, 'w') as w:
        w.writelines((f'{k} {v}\n' for k, v in log.items()))


def update_tracklist(anime_name, episodes, append=True):
    log = read_log(logfile=config.ongoingfile)
    if anime_name in log:
        write_log(anime_name,
                  episodes,
                  append=append,
                  logfile=config.ongoingfile)


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
        return iter()
    ranges = range_str.split(',')
    try:
        for r in ranges:
            if '-' in r:
                rng = r.split('-')
                if len(rng) > 2:
                    outputs.prompt_val('Incorrect formatting', r, 'error')
                    raise SystemExit
                yield from range(int(rng[0]), int(rng[1]) + 1)
            else:
                yield int(r)
    except ValueError as e:
        outputs.error_info(f'Incorrect formatting: use integers for episodes')
        outputs.error_tag(e)
        raise SystemExit
