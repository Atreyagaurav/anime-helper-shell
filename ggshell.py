#!/usr/bin/env python
import cmd
import main as commands
import readline
import sys

class GGshell(cmd.Cmd):
    prompt = "gogoanime >>"
    indentchars = cmd.IDENTCHARS
    def emptyline(self):
        pass

    def completedefault(self, text, line, start, end):
        lists = set(commands.read_log().keys()).union(set(commands.read_cache(complete=True)))
        pname = line.split()[-1]
        plen = len(pname)
        match = filter(lambda t: t.startswith(pname),lists)
        return list(map(lambda l: l[plen-len(text):],match))
    
    def do_exit(self,inp):
        """Exit this interactive shell."""
        return True

    def do_url(self,inp):
        """Downloads the anime episode from given gogoanime url
USAGE: url [GOGOANIME-URL]
        GOGOANIME-URL : Url of the episode from gogoanime website.
"""
        commands.download_from_url(inp.split())

    def complete_url(self, text, line, *ignored):
        url = commands.get_anime_url('')
        if url in line:
            return self.completedefault(text, line.split('/')[-1], *ignored)
        else:
            return [commands.get_anime_url('')]

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
        """Display the log information. Pass Anime name or keywords to filter the log. (supports python regex)

USAGE: log [KEYWORDS]
        KEYWORDS     : Name of the anime, or regex to filter the log.
        """
        commands.anime_log(inp.split())

    def do_info(self, inp):
        """Show the information of the anime, if you have just searched something, you can see their info to test if that's what you are searching for.

USAGE: info [ANIME-NAME]
        ANIME-NAME     : Name of the anime, or choice number; defaults to 0
        """
        commands.anime_info(inp.split())
    
    
    def do_check(self, inp):
        """Check if the given episodes range are downloaded and available offline. 
Do not use this when simple commands like ls and tree are enough, as it also checks the file online to make sure extensions match.
        """
        commands.check_anime(inp.split())

    def help_animename(self, *args):
        print("""
ANIME-NAME   - Name of the anime or url or choice number. 
               It must be same as the name on gogoanime address bar unless
                 you are searching anime, or using the results from search.
               If you exclude this argument, the first choice from last
                 listed animes or the anime last played/downloaded will
                 be used. (first line of anime cachefile)
               You can put a choice number starting from 0 if you want to
                 choose any anime from last anime lists. Like from results 
                 of 'search' command.
        """)

    def help_episodesrange(self, *args):
        print("""
RANGE   - Range of the episodes; defaults to all episodes if not
            specified.
          For 'continue' command, defaults to unwatched episodes.""")

    def help_summary(self, *args):
        print(f"""Command Line Interface for anime available in gogoanime
 website.

Usage: COMMAND [ANIME-NAME] [RANGE]

Launching with no arguments will launch an interactive interface. 

COMMAND    - Command to execute, see details below for available commands.
ANIME-NAME - Name of the anime or url or choice number. 
             It must be same as the name on gogoanime address bar unless
               you are searching anime, or using the results from search.
             If you exclude this argument, the first choice from last
               listed animes or the anime last played/downloaded will
               be used. (first line of anime cachefile)
             You can put a choice number starting from 0 if you want to
               choose any anime from last anime lists. Like from results 
               of 'search' command.
RANGE      - Range of the episodes; defaults to all episodes if not
               specified.
             For 'continue' command, defaults to unwatched episodes.

AVAILABLE COMMANDS:
help     - Display this message.
url      - Download the video from provided URL.
download - Download specified anime(episodes).
check    - Check if specified anime(episodes) has missing episodes files.
           Do not use this when simple commands like tree or ls can give 
           you information as this command checks the files online.
list     - Just list the available episodes range.
play     - Play the episodes in mpv.
continue - Continue playing given anime from your last watch.
search   - Search the anime list from given name/keywords.
info     - Get the information about the anime.
log      - print the log. Regex for filtering the log can be given as a argument.
watched  - Add the episodes as watched in log, if you watched them elsewhere. 

Example Usage:
    check one-piece 1-10
    download one-piece 1-2,5
    info one-piece
    search "One Piece Movie"
    list https://gogoanime.so/category/one-piece
    url https://gogoanime.so/one-piece-episode-1
""")


if __name__ == '__main__':
    if len(sys.argv)==1:
        GGshell().cmdloop("Welcome, This is the CLI interactive for gogoanime.\nType help for more")
    else:
        GGshell().onecmd(" ".join(sys.argv[1:]))
