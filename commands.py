#!/usr/bin/env python
import os
import re
import sys

import subprocess
import time
import html2text

import config
import gogoanime
import utils
import outputs


def set_quality(quality):
    if quality.isnumeric():
        config.QUALITY_PREFERENCE = int(quality)
    elif quality.isalnum():
        if re.match(r'[0-9]+p', quality):
            config.QUALITY_PREFERENCE = int(quality[:-1])
        else:
            outputs.prompt_val('Invalid quality format', quality, 'error')
    else:
        outputs.normal_info(f'Current quality: {quality}')


def toggle_fullscreen(value):
    if value.lower() in ['on', 'yes']:
        config.fullscreen = True
        config.compile_ext_player_command()
    elif value.lower() in ['off', 'no']:
        config.fullscreen = False
        config.compile_ext_player_command()
    else:
        outputs.prompt_val('Incorrect Argument', value, 'error')
    outputs.prompt_val('External Player command',
                       " ".join(config.ext_player_command))


def set_geometry(value):
    if re.match(r'^([0-9]+-?)+$', value):
        config.geometry = value
        config.compile_ext_player_command()
    else:
        outputs.prompt_val('Incorrect Argument', value, 'error')
    outputs.prompt_val('External Player command',
                       " ".join(config.ext_player_command))


def anime_log(args):
    outputs.bold_info('Watched\t\tAnime Name')
    log_args = dict()
    if len(args) == 0:
        pass
    elif args[0].isnumeric():
        log_args['number'] = int(args[0])
    else:
        log_args['pattern'] = re.compile(args[0])
        if len(args) == 2:
            log_args['number'] = int(args[1])
    logs = utils.read_log(**log_args).items()
    for k, v in logs:
        outputs.normal_info(f'{v}\t\t{k}')


def play_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        url = gogoanime.get_episode_url(name, e)
        stream_from_url(url, name, e)


def update_log(args):
    anime_name, episodes = read_args(args)
    episodes = utils.compress_range(episodes)
    utils.write_log(anime_name, episodes)
    utils.update_tracklist(anime_name, episodes)


def edit_log(args):
    anime_name, episodes = read_args(args)
    utils.write_log(anime_name, utils.compress_range(episodes), append=False)


def continue_play(args):
    name, episodes = read_args(args)
    watched = utils.read_log().get(name)
    outputs.prompt_val('Watched', watched, 'success')
    if not watched:
        last = 0
    else:
        last = int(watched.split('-')[-1])
    play_anime(
        [name,
         utils.compress_range(filter(lambda e: e > last, episodes))])


def download_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        url = gogoanime.get_episode_url(name, e)
        download_from_url(url, name, e)


def check_anime(args):
    name, episodes = read_args(args)
    unavail_eps = []
    for e in episodes:
        url = gogoanime.get_episode_url(name, e)
        outputs.normal_info('Testing:', url)
        durl, ext = gogoanime.get_direct_video_url(url)
        if not durl:
            raise SystemExit('Url for the file not found')
        if not os.path.exists(
                os.path.join(config.anime_dir, f'./{name}/ep{e:02d}.{ext}')):
            unavail_eps.append(e)
    if len(unavail_eps) == 0:
        outputs.success_info(
            'All episodes in given range are locally available')
    else:
        outputs.prompt_val('Missing episodes',
                           utils.compress_range(unavail_eps), 'warning')


def read_args(args, episodes=True):
    if len(args) == 0:
        name = utils.read_cache()
    elif args[0].isnumeric():
        name = utils.read_cache(int(args[0]))
        outputs.prompt_val('Name', name)
    elif '/' in args[0]:
        name = args[0].strip('/').split('/')[-1]
    else:
        name = gogoanime.process_anime_name(args[0])
        if not gogoanime.verify_anime_exists(name):
            outputs.prompt_val(f'Anime with the name doesn\'t exist', args[0],
                               'error')
            raise SystemExit

    if not name:
        outputs.error_info('Numbers choice invalid, or invalid context.')
        raise SystemExit

    if not episodes:
        return name
    if len(args) <= 1:
        outputs.warning_info('Episodes range not given defaulting to all')
        available_rng = gogoanime.get_episodes_range(
            gogoanime.get_anime_url(name))
        outputs.prompt_val('Available episodes', available_rng)
        episodes = utils.extract_range(available_rng)
    elif len(args) == 2:
        episodes = utils.extract_range(args[1])
    else:
        outputs.error_info('Too many arguments.\n')
        outputs.normal_info(__doc__)
        raise SystemExit
    return name, episodes


def list_episodes(args):
    name, episodes = read_args(args)
    if len(sys.argv) == 4:
        eps = set(episodes)
        avl_eps = set(
            utils.extract_range(
                gogoanime.get_episodes_range(gogoanime.get_anime_url(name))))
        res = eps.intersection(avl_eps)
        result = utils.compress_range(res)
        outputs.prompt_val(f'Available episodes', result)
    outputs.prompt_val(f'Watched episodes', utils.read_log(name), 'success')
    utils.write_cache(name)


def search_anime(args):
    name = " ".join(args)
    url = config.search_t.substitute(name=name)
    soup = utils.get_soup(url)
    plist = soup.find('ul', {'class': 'pagination-list'})
    utils.clear_cache()

    def search_results(s):
        all_res = s.find('ul', {'class': 'items'})
        for list_item in all_res.find_all('li'):
            an = list_item.p.a['href'].split('/')[-1]
            utils.write_cache(an, append=True)
            outputs.normal_info(an, end='  \t')
            outputs.normal_info(list_item.p.a.text)

    search_results(soup)
    if plist:
        for list_item in plist.find_all('li', {'class': None}):
            url = config.search_page_t.substitute(name=name,
                                                  page=list_item.a.text)
            soup = utils.get_soup(url)
            search_results(soup)


def import_from_mal(username):
    pass


def anime_info(args):
    name = read_args(args, episodes=False)
    soup = utils.get_soup(gogoanime.get_anime_url(name))
    info = soup.find('div', {'class': 'anime_info_body'})
    h = html2text.HTML2Text()
    h.ignore_links = True
    for t in info.find_all('p', {'class': 'type'}):
        outputs.normal_info(h.handle(t.decode_contents()), end="")


def download_from_url(gogo_url, anime_name=None, episode=None):
    if not anime_name or not episode:
        anime_name, episode = gogoanime.parse_gogo_url(gogo_url)
    os.makedirs(os.path.join(config.anime_dir, f'./{anime_name}'),
                exist_ok=True)
    outputs.prompt_val('Downloading', gogo_url)
    durl, ext = gogoanime.get_direct_video_url(gogo_url)
    if not durl:
        outputs.error_info('Url for the file not found')
        raise SystemExit
    if ext == 'm3u8':
        m3u8_url = utils.get_m3u8_stream(durl)
        utils.download_m3u8(
            m3u8_url,
            os.path.join(config.anime_dir,
                         f'./{anime_name}/ep{episode:02d}.{ext}'))
    else:
        utils.download_file(
            durl,
            os.path.join(config.anime_dir,
                         f'./{anime_name}/ep{episode:02d}.{ext}'))


def stream_from_url(url, anime_name=None, episode=None):
    if not anime_name or not episode:
        anime_name, episode = gogoanime.parse_gogo_url(url)
    outputs.normal_info('Getting Streaming Link:', url)
    durl, ext = gogoanime.get_direct_video_url(url)
    if not durl:
        outputs.error_info('Url for the file not found')
        raise SystemExit
    if ext == 'm3u8':
        durl = utils.get_m3u8_stream(durl)
    outputs.prompt_val(f'Stream link', durl, 'success')
    try:
        for i in range(11):
            outputs.normal_info(
                f'\rOpening External Player in: {1-i/10:1.1f} sec.', end='')
            time.sleep(0.1)
    except KeyboardInterrupt:
        outputs.warning_info('\nInturrupted, Exiting...')
        raise SystemExit
    outputs.normal_info()
    while True:
        t1 = time.time()
        ret_val = subprocess.call(" ".join(config.ext_player_command + [durl]),
                                  shell=True)
        if ret_val == 2:  # mpv error code
            outputs.error_info('Couldn\'t open the stream.')
            if input("retry?<Y/n>") == '':
                continue
            else:
                raise SystemExit
        if (time.time() - t1) > (
                5 * 60
        ):  # 5 minutes watchtime at least, otherwise consider it unwatched.
            # TODO: use direct communication with mpv to know if episode was watched.
            utils.write_log(anime_name, episode)
            utils.update_tracklist(anime_name, episode)
            utils.write_cache(anime_name)
        return


def track_anime(args):
    """Put an anime into the track list"""
    anime_name, episodes = read_args(args)
    watched_episodes = utils.read_log(anime_name)
    if watched_episodes is None:
        outputs.warning_info(
            'Log entry not found. Setting only new episodes for tracking.')
        episodes = utils.compress_range(episodes)
    else:
        outputs.prompt_val(f'Watched', watched_episodes, 'success')
        episodes = watched_episodes
    utils.write_log(anime_name,
                    episodes,
                    append=False,
                    logfile=config.ongoingfile)


def untrack_anime(anime_name):
    """Remove an anime from the track list"""
    anime_list = utils.read_log(logfile=config.ongoingfile)
    if anime_name in anime_list:
        anime_list.pop(anime_name)
    else:
        return
    with open(config.ongoingfile, 'w') as w:
        for k, v in anime_list.items():
            w.write(f'{k} {v}\n')


def list_tracked():
    anime_list = utils.read_log(logfile=config.ongoingfile)
    for anime, episodes in anime_list.items():
        outputs.normal_info(f'{anime} : {episodes}')


def get_updates(anime_name=''):
    """Check and display the updates on the tracked anime list."""
    if anime_name == '':
        anime_list = utils.read_log(logfile=config.ongoingfile)
    else:
        anime_list = {
            anime_name:
            utils.read_log(anime_name=anime_name, logfile=config.ongoingfile)
        }
    updates = {}
    for anime, episodes in anime_list.items():
        new_episodes = gogoanime.get_episodes_range(
            gogoanime.get_anime_url(anime))
        new = set(utils.extract_range(new_episodes)).difference(
            set(utils.extract_range(episodes)))
        if len(new) > 0:
            updates[anime] = new
    if len(updates) == 0:
        outputs.normal_info("No new episodes released.")
        return
    if anime_name == '':
        outputs.prompt_val(f'anime(s) has new episodes.',
                           len(updates),
                           'success',
                           sep=" ",
                           reverse=True)
        outputs.normal_info('-' * 50)
    for anime, episodes in updates.items():
        outputs.normal_info(anime, end='\n\t')
        outputs.success_tag(len(episodes), end=' ')
        outputs.prompt_val('new episodes', utils.compress_range(episodes),
                           'success')
