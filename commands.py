#!/usr/bin/env python
import os
import re
import time
import html2text
import webbrowser

import config
import utils
import outputs
import notification

import players
import sources


player_module = getattr(players, config.ext_player)
player_module.compile_command(
    flags=config.ext_player_flags,
    fullscreen=config.ext_player_fullscreen
)
anime_source_module = getattr(sources, config.anime_source)


def set_quality(quality):
    if quality.isnumeric():
        config.video_quality = int(quality)
    elif quality.isalnum():
        if re.match(r"[0-9]+p", quality):
            config.video_quality = int(quality[:-1])
        else:
            outputs.prompt_val("Invalid quality format", quality, "error")
    else:
        outputs.normal_info(f"Current quality: {quality}")


def toggle_fullscreen(value):
    if value.lower() in ["on", "yes", "true"]:
        config.ext_player_fullscreen = True
        player_module.compile_command(
            flags=config.ext_player_flags,
            fullscreen=True
        )
    elif value.lower() in ["off", "no", "false"]:
        config.ext_player_fullscreen = False
        player_module.compile_command(
            flags=config.ext_player_flags,
            fullscreen=False
        )
    else:
        outputs.prompt_val("Incorrect Argument", value, "error")
    outputs.prompt_val("External Player command",
                       player_module.get_player_command())


def set_geometry(value):
    if re.match(r"^([0-9]+-?)+$", value):
        player_module.set_geometry(value)
        player_module.compile_command(
            flags=config.ext_player_flags,
            fullscreen=config.ext_player_fullscreen
        )
    else:
        outputs.prompt_val("Incorrect Argument", value, "error")
    outputs.prompt_val("External Player command",
                       player_module.get_player_command())


def anime_log(args):
    log_args = dict()
    if len(args) == 0:
        pass
    elif args[0].isnumeric():
        log_args["number"] = int(args[0])
    else:
        log_args["pattern"] = re.compile(args[0])
        if len(args) == 2:
            log_args["number"] = int(args[1])
    logs = utils.read_log(**log_args)
    ongoing = utils.read_log(logfile=config.ongoingfile)
    if len(logs) == 0:
        if len(args) == 0:
            outputs.warning_info("No log entries found.")
        else:
            outputs.prompt_val("Log entries not found for arguments", args[0],
                               "error")
        return
    outputs.bold_info("Watched\t\tAnime Name")
    for k, log in logs.items():
        outputs.normal_info(utils.Log(log).show(), end=" ")
        if k in ongoing:
            outputs.warning_tag("TRACKED", end="")
        outputs.normal_info()


def check_canon(args):
    name, episodes = read_args(args, episodes=False)
    eps = utils.canon_episodes(name, episodes)
    outputs.normal_info(eps)


def play_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        url = anime_source_module.get_episode_url(name, e)
        stream_from_url(url, name, e)


def play_local_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        path = utils.get_episode_path(name, e, check=True)
        if not path:
            outputs.prompt_val("File not found locally", f"{name}:ep-{e}",
                               "error")
            continue
        stream_from_url(path, name, e, local=True)


def watch_episode_in_web(args):
    name, episodes = read_args(args, episodes=None)
    if not episodes:
        url = anime_source_module.get_anime_url(name)
        webbrowser.open_new_tab(url)
        return
    for e in episodes:
        url = anime_source_module.get_episode_url(name, e)
        webbrowser.open_new_tab(url)
        choice = input(f"did you watch the episode {e}? <Y/n>")
        if not choice.strip() or choice.strip() in 'Yy':
            utils.write_log(name, e)
            utils.update_tracklist(name, e)
            utils.write_cache(name)
            utils.update_watchlater(name, e)


def update_log(args):
    anime_name, episodes = read_args(args)
    episodes = utils.compress_range(episodes)
    utils.write_log(anime_name, episodes)
    utils.update_tracklist(anime_name, episodes)
    utils.write_cache(anime_name)
    utils.update_watchlater(anime_name, episodes)


def edit_log(args):
    anime_name, episodes = read_args(args)
    utils.write_log(anime_name, utils.compress_range(episodes), append=False)


def continue_play(args, play_func=play_anime):
    name, _ = read_args(args, episodes=False)
    log = utils.Log(utils.read_log().get(name))
    watch_later = utils.read_log(name, logfile=config.watchlaterfile)
    if watch_later:
        episodes = utils.extract_range(utils.Log(watch_later).eps)
    else:
        _, episodes = read_args(args)
    outputs.prompt_val("Watched",
                       log._eps, "success", end='\t')
    outputs.normal_info(log.last_updated_fmt)
    if not log.eps:
        last = 0
    else:
        last = int(re.split('-|,', log.eps)[-1])
    to_play = utils.compress_range(filter(lambda e: e > last, episodes))
    if to_play.strip():
        play_func([name, to_play])
    else:
        unsave_anime(name)


def download_anime(args):
    name, episodes = read_args(args)
    for e in episodes:
        url = anime_source_module.get_episode_url(name, e)
        download_from_url(url, name, e)


def check_anime(args):
    name, episodes = read_args(args)
    unavail_eps = []
    for e in episodes:
        url = anime_source_module.get_episode_url(name, e)
        outputs.normal_info("Testing:", url)
        durl, ext = anime_source_module.get_direct_video_url(url)
        if not durl:
            raise SystemExit("Url for the file not found")
        if not os.path.exists(
                os.path.join(config.anime_dir, f"./{name}/ep{e:02d}.{ext}")):
            unavail_eps.append(e)
    if len(unavail_eps) == 0:
        outputs.success_info(
            "All episodes in given range are locally available")
    else:
        outputs.prompt_val("Missing episodes",
                           utils.compress_range(unavail_eps), "warning")


def read_args(args, episodes=True, verbose=True):
    if len(args) == 0:
        name = utils.read_cache()
    elif len(args) == 1 and args[0].isnumeric():
        name = utils.read_cache(int(args[0]))
        if verbose:
            outputs.prompt_val("Name", name)
    elif "/" in args[0]:
        name = args[0].strip("/").split("/")[-1]
    else:
        name = anime_source_module.process_anime_name(args[0].strip('"'))
        if not anime_source_module.verify_anime_exists(name):
            outputs.prompt_val("Anime with the name doesn't exist", args[0],
                               "error")
            raise SystemExit

    if not name:
        outputs.error_info("Numbers choice invalid, or invalid context.")
        raise SystemExit

    if len(args) <= 1:
        if episodes:
            if verbose:
                outputs.warning_info("Episodes range not given defaulting to all")
            available_rng = anime_source_module.get_episodes_range(
                anime_source_module.get_anime_url(name))
            if verbose:
                outputs.prompt_val("Available episodes", available_rng)
            eps = utils.extract_range(available_rng)
        else:
            eps = None
    elif len(args) == 2:
        eps = utils.extract_range(args[1])
    else:
        outputs.error_info("Too many arguments.\n")
        outputs.normal_info(__doc__)
        raise SystemExit
    return name, eps


def list_episodes(args):
    name, _ = read_args(args, episodes=False)
    available_rng = anime_source_module.get_episodes_range(anime_source_module.get_anime_url(name))
    if len(args) == 2:
        _, episodes = read_args(args)
        eps = set(episodes)
        avl_eps = set(utils.extract_range(available_rng))
        res = eps.intersection(avl_eps)
        available_rng = utils.compress_range(res)
    outputs.prompt_val("Available episodes", available_rng)
    log = utils.Log(utils.read_log(name))
    outputs.prompt_val("Watched episodes", log.eps, "success", end=' ')
    outputs.normal_info(log.last_updated_fmt)
    utils.write_cache(name)


def list_local_episodes(args):
    in_dict = utils.get_local_episodes(*args)
    out_dict = dict()
    for anime, eps in in_dict.items():
        new_eps = utils.compress_range(utils.extract_range(eps))
        if new_eps != "":
            out_dict[anime] = new_eps
    empties = set(in_dict).difference(set(out_dict))
    if len(out_dict) == 0:
        outputs.warning_info("No local entries found.")
    else:
        outputs.bold_info("Episodes\tAnime Name")
        for k, v in out_dict.items():
            outputs.normal_info(f"{v}\t\t{k}")
    if len(empties) > 0:
        outputs.warning_info("Directories without Episodes:")
        outputs.warning_info(", ".join(empties))


def search_anime(args):
    name = " ".join(args)
    anime_source_module.search_anime(name)


def latest():
    utils.display_anime_eps_list(anime_source_module.home_page())


def new():
    utils.display_anime_eps_list(anime_source_module.new_page())


def import_from_mal(username):
    # TODO : use MAL username to import his completed and other lists.
    pass


def anime_info(args):
    name, _ = read_args(args, episodes=False)
    soup = utils.get_soup(anime_source_module.get_anime_url(name))
    info = soup.find("div", {"class": "anime_info_body"})
    h = html2text.HTML2Text()
    h.ignore_links = True
    for t in info.find_all("p", {"class": "type"}):
        outputs.normal_info(h.handle(t.decode_contents()), end="")


def download_from_url(url, anime_name=None, episode=None):
    if not anime_name or not episode:
        anime_name, episode = anime_source_module.parse_url(url)
    os.makedirs(os.path.join(config.anime_dir, f"./{anime_name}"),
                exist_ok=True)
    outputs.prompt_val("Downloading", url)
    durl, ext = anime_source_module.get_direct_video_url(url)
    if not durl:
        outputs.error_info("Url for the file not found")
        raise SystemExit
    if ext == ".m3u8":
        utils.download_m3u8(
            durl, utils.get_episode_path(anime_name, episode, make=True))
    else:
        utils.download_file(
            durl,
            utils.get_episode_path(anime_name, episode, ext=ext, make=True))


def stream_from_url(url, anime_name=None, episode=None, *, local=False):
    if not anime_name or not episode:
        anime_name, episode = anime_source_module.parse_url(url)
    if local:
        durl = url
        _, ext = os.path.splitext(durl)
    else:
        outputs.normal_info("Getting Streaming Link:", url)
        durl, ext = anime_source_module.get_direct_video_url(url)
        if not durl:
            outputs.error_info("Url for the file not found")
            raise SystemExit
    outputs.prompt_val("Stream link", durl, "success")
    try:
        if config.ext_player_confirm:
            choice = input(f"Open {config.ext_player} Player? <Y/n>")
            if choice == "" or choice.lower() == "y":
                pass
            else:
                raise SystemExit
        else:
            for i in range(11):
                outputs.normal_info(
                    f"\rOpening External Player in: {1-i/10:1.1f} sec.",
                    end="")
                time.sleep(0.1)
            outputs.normal_info()
        retval = player_module.play_media(
            durl, title=f"Ganime:{anime_name}:ep-{episode}{ext}")
        if retval:
            utils.write_log(anime_name, episode)
            utils.update_tracklist(anime_name, episode)
            utils.write_cache(anime_name)
            utils.update_watchlater(anime_name, episode)
            return
    except KeyboardInterrupt:
        outputs.warning_info("\nInturrupted, Exiting...")
        raise SystemExit
    outputs.normal_info()


def save_anime(args):
    """Put the anime into watch later list."""
    anime_name, eps = read_args(args)
    watched = utils.read_log(anime_name)
    if watched:
        watched_eps = utils.extract_range(utils.Log(watched).eps)
    else:
        watched_eps = []
    save_eps = set(eps).difference(set(watched_eps))
    if not save_eps:
        outputs.warning_info('Already watched the provided episodes.')
        return
    utils.write_log(anime_name,
                    utils.compress_range(save_eps),
                    append=True,
                    logfile=config.watchlaterfile)


def track_anime(args):
    """Put an anime into the track list"""
    anime_name, episodes = read_args(args, episodes=False)
    log = utils.read_log(anime_name)
    if log is None:
        outputs.warning_info(
            "Log entry not found.")
        if not episodes:
            _, episodes = read_args(args)
        episodes = utils.compress_range(episodes)
    else:
        episodes = utils.Log(log).eps
        outputs.prompt_val("Watched", episodes, "success")
    utils.write_log(anime_name,
                    episodes,
                    append=False,
                    logfile=config.ongoingfile)


def untrack_anime(anime_name):
    """Remove an anime from the track list"""
    utils.remove_anime_from_log(anime_name, logfile=config.ongoingfile)


def unsave_anime(anime_name):
    """Remove an anime from the saved list"""
    utils.remove_anime_from_log(anime_name, logfile=config.watchlaterfile)


def unlog_anime(anime_name):
    utils.remove_anime_from_log(anime_name)


def list_tracked():
    anime_list = utils.read_log(logfile=config.ongoingfile)
    for anime, log in anime_list.items():
        outputs.normal_info(utils.Log(log).show())


def list_saved_anime():
    anime_list = utils.read_log(logfile=config.watchlaterfile)
    for anime, log in anime_list.items():
        outputs.normal_info(utils.Log(log).show())


def anime_updates(anime_name=""):
    """Check and display the updates on the tracked anime list."""
    if anime_name == "":
        anime_list = utils.read_log(logfile=config.ongoingfile)
    else:
        anime_list = {
            anime_name:
            utils.read_log(anime_name=anime_name, logfile=config.ongoingfile)
        }
    updates = {}
    for anime, log in anime_list.items():
        episodes = log.split()[2]  # FIX: use log object
        new_episodes = anime_source_module.get_episodes_range(
            anime_source_module.get_anime_url(anime))
        new = set(utils.extract_range(new_episodes)).difference(
            set(utils.extract_range(episodes)))
        if len(new) > 0:
            updates[anime] = new
    return updates


def get_updates(anime_name=""):
    """Check and display the updates on the tracked anime list."""
    updates = anime_updates(anime_name)
    if len(updates) == 0:
        outputs.normal_info("No new episodes released.")
        return
    if anime_name == "":
        outputs.prompt_val(
            "anime(s) has new episodes.",
            len(updates),
            "success",
            sep=" ",
            reverse=True,
        )
        outputs.normal_info("-" * 50)
    for anime, episodes in updates.items():
        outputs.normal_info(anime, end="\n\t")
        outputs.success_tag(len(episodes), end=" ")
        outputs.prompt_val("new episodes", utils.compress_range(episodes),
                           "success")


def notify_update(anime_name=""):
    updates = anime_updates(anime_name)
    notification.episodes_update(updates)
