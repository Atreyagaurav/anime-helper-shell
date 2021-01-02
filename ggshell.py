#!/usr/bin/env python
import cmd
import sys
import os
import subprocess
import re

from requests.exceptions import ConnectionError, ConnectTimeout

import commands
import gogoanime
import utils
import config
import outputs


class GGshell(cmd.Cmd):
    # These are overriden from cmd.Cmd
    # ANSII scapes for orage bg
    prompt = "\x1b[43mgogoanime\x1b[0m >>"
    # to have '-' character in my commands
    identchars = cmd.Cmd.identchars + '-'
    ruler = '-'
    misc_header = 'Other Help Topics'

    def onecmd(self, ind):
        if ind == 'EOF':
            outputs.normal_info()
            return
        try:
            return super().onecmd(ind)
        except (SystemExit, KeyboardInterrupt):
            outputs.normal_info()
        except (ConnectionError, ConnectTimeout):
            outputs.error_info('Slow or no Internet connection. Try again.')

    def cmdloop(self, intro=None):
        """Repeatedly issue a prompt, accept input, parse an initial prefix
        off the received input, and dispatch to action methods, passing them
        the remainder of the line as argument.

        """

        self.preloop()
        if self.use_rawinput and self.completekey:
            try:
                import readline
                self.old_completer = readline.get_completer()
                readline.set_completer(self.complete)
                readline.parse_and_bind(self.completekey + ": complete")
            except ImportError:
                pass
        try:
            if intro is not None:
                self.intro = intro
            if self.intro:
                self.stdout.write(str(self.intro) + "\n")
            stop = None
            while not stop:
                if self.cmdqueue:
                    line = self.cmdqueue.pop(0)
                else:
                    try:
                        if self.use_rawinput:
                            try:
                                line = input(self.prompt)
                            except EOFError:
                                line = 'EOF'
                        else:
                            self.stdout.write(self.prompt)
                            self.stdout.flush()
                            line = self.stdin.readline()
                            if not len(line):
                                line = 'EOF'
                            else:
                                line = line.rstrip('\r\n')
                    except KeyboardInterrupt:
                        self.stdout.write('\n^C\n')
                        continue
                line = self.precmd(line)
                stop = self.onecmd(line)
                stop = self.postcmd(stop, line)
            self.postloop()
        finally:
            if self.use_rawinput and self.completekey:
                try:
                    import readline
                    readline.set_completer(self.old_completer)
                except ImportError:
                    pass

    def preloop(self):
        try:
            import readline
            if os.path.exists(config.historyfile):
                readline.read_history_file(config.historyfile)
            self.old_completers = readline.get_completer_delims()
            readline.set_completer_delims(
                re.sub(r'-|:|/', '', self.old_completers))
        except ImportError:
            pass

    def postloop(self):
        try:
            import readline
            readline.set_history_length(1000)
            readline.write_history_file(config.historyfile)
            readline.set_completer_delims(self.old_completers)
        except ImportError:
            pass

    def emptyline(self):
        pass

    def completedefault(self, text, line, start, end):
        if re.match(r'([a-z-]+ +){2,}', line):
            return []
        lists = set(utils.read_log().keys()).union(
            set(utils.read_cache(complete=True)))
        match = filter(lambda t: t.startswith(text), lists)
        return list(match)

    def do_help(self, topic):
        if len(topic) == 0:
            import __init__
            outputs.normal_info(__init__.__doc__)
        super().do_help(topic)

    # From here my commands start

    def do_exit(self, inp):
        """Exit this interactive shell."""
        return True

    def do_history(self, inp):
        """show the history of the commands.
        """
        try:
            import readline
            for j in range(1, readline.get_current_history_length() + 1):
                h = readline.get_history_item(j)
                if re.match(inp, h):
                    outputs.normal_info(f'{j:3d}:  {h}')
        except ImportError:
            pass

    def do_shell(self, inp):
        """Execute shell commands
        """
        subprocess.call(inp, shell=True)

    def do_quality(self, inp):
        """Sets the quality for the anime.
        """
        commands.set_quality(inp)

    def complete_quality(self, text, *ignored):
        possibilities = ['360p', '480p', '720p', '1080p']
        match = filter(lambda t: t.startswith(text), possibilities)
        return list(match)

    def do_geometry(self, inp):
        """Sets the geometry for the external player.
        """
        commands.set_geometry(inp)

    def do_fullscreen(self, inp):
        """Toggles the fullscreen setting for external player.
        """
        commands.toggle_fullscreen(inp)

    def complete_fullscreen(self, text, *ignored):
        possibilities = ['yes', 'no', 'on', 'off']
        match = filter(lambda t: t.startswith(text), possibilities)
        return list(match)

    def do_untrack(self, inp):
        """Put the given anime into the active track list.

USAGE: untrack [ANIME-NAME]
        ANIME-NAME     : Name of the anime
        """
        commands.untrack_anime(inp)

    def complete_untrack(self, text, line, start, end):
        if re.match(r'([a-z-]+ +){2,}', line):
            return []
        lists = utils.read_log(logfile=config.ongoingfile).keys()
        match = filter(lambda t: t.startswith(text), lists)
        return list(match)

    def do_track(self, inp):
        """Put the given anime into the active track list.

USAGE: track [ANIME-NAME] [EPISODES-RANGE]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        EPISODES-RANGE : Range of the episodes, defaults to all
        """
        commands.track_anime(inp.split())

    def do_tracklist(self, inp):
        """Lists all the animes on the track list.

USAGE: tracklist
        """
        commands.list_tracked()

    def do_updates(self, inp):
        """Get the updates for new episode releases.

USAGE: updates [ANIME-NAME]
        ANIME-NAME     : Name of the anime
        """
        commands.get_updates(inp.strip())

    complete_updates = complete_untrack

    def do_notify(self, inp):
        """Get the updates for new episode releases in notification.

USAGE: notify [ANIME-NAME]
        ANIME-NAME     : Name of the anime
        """
        commands.notify_update(inp.strip())

    complete_notify = complete_untrack

    def do_url(self, inp):
        """Downloads the anime episode from given gogoanime url
USAGE: url [GOGOANIME-URL]
        GOGOANIME-URL : Url of the episode from gogoanime website.
"""
        commands.download_from_url(inp)

    def do_streamurl(self, inp):
        """Streams the anime episode from given gogoanime url
USAGE: streamurl [GOGOANIME-URL]
        GOGOANIME-URL : Url of the episode from gogoanime website.
"""
        commands.stream_from_url(inp)

    def complete_url(self, text, line, *ignored):
        lists = set(utils.read_log().keys()).union(
            set(utils.read_cache(complete=True)))
        urls = map(lambda name: gogoanime.get_episode_url(name, ''), lists)
        match = filter(lambda t: t.startswith(text), urls)
        return list(match)

    complete_streamurl = complete_url

    def do_download(self, inp):
        """Download the anime episodes in given range

USAGE: download [ANIME-NAME] [EPISODES-RANGE]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        EPISODES-RANGE : Range of the episodes, defaults to all
        """
        commands.download_anime(inp.split())

    def do_list(self, inp):
        """List the episodes available for the given anime.

USAGE: list [ANIME-NAME] [EPISODES-RANGE]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        EPISODES-RANGE : Range of the episodes, defaults to all
        """
        commands.list_episodes(inp.split())

    def do_play(self, inp):
        """Play the given episodes of the given anime.

USAGE: play [ANIME-NAME] [EPISODES-RANGE]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        EPISODES-RANGE : Range of the episodes, defaults to all
        """
        commands.play_anime(inp.split())

    def do_watched(self, inp):
        """Update the log so that the given anime (& episodes) are deemed watched.

USAGE: watched [ANIME-NAME] [EPISODES-RANGE]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        EPISODES-RANGE : Range of the episodes, defaults to all
        """
        commands.update_log(inp.split())

    def do_edit(self, inp):
        """Edit the log so that the given anime (& episodes) replace the previous log information with new.

USAGE: edit [ANIME-NAME] [EPISODES-RANGE]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        EPISODES-RANGE : Range of the episodes, defaults to all
        """
        commands.edit_log(inp.split())

    def do_continue(self, inp):
        """Play the given anime's unwatched episodes from the start.

USAGE: continue [ANIME-NAME]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        """
        commands.continue_play(inp.split())

    def do_search(self, inp):
        """Search the given keywords in the gogoanime anime list.

USAGE: search [KEYWORDS]
        KEYWORDS     : Name of the anime, in english or japanese.
                       You can use this search result as choice number in
                        next command. first choice is 1.
        """
        commands.search_anime(inp.split())

    def do_log(self, inp):
        """Display the log information.
Pass Anime name or keywords to filter the log. (supports python regex)

USAGE: log [KEYWORDS] [NUMBER]
        KEYWORDS     : Name of the anime, or regex to filter the log.
        NUMBER       : Number of log items to be shown.
        """
        commands.anime_log(inp.split())

    def do_info(self, inp):
        """Show the information of the anime, if you have just searched
something, you can see their info to test if that's what you are searching
for.

USAGE: info [ANIME-NAME]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        """
        commands.anime_info(inp.split())

    def do_check(self, inp):
        """Check if the given episodes range are downloaded and available
offline.
Do not use this when simple commands like ls and tree are enough, as it
also checks the file online to make sure extensions match.
        """
        commands.check_anime(inp.split())


if __name__ == '__main__':
    if len(sys.argv) == 1:
        gshell = GGshell()
        gshell.cmdloop("""Welcome, This is the CLI interactive for gogoanime.
Type help for more.""")
    else:
        GGshell().onecmd(" ".join(sys.argv[1:]))
