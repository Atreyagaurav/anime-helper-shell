"""Command Line Interface for anime available in gogoanime website.

Usage:
 - One time usage:
ggshell.py COMMAND [ANIME-NAME] [RANGE]
 - Shell usage:
COMMAND [ANIME-NAME] [RANGE]

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
debug    - Launch the debug shell.
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
log      - print the log. Regex for filtering the log can be given as an
          argument.
watched  - Add the episodes as watched in log, if you watched them elsewhere.
track    - Put the anime on track list .
updates  - See if any anime on the track list have updates on new episodes.
notify   - Get the updates in notification, good for scheduled check.

Example Usage:
    check one-piece 1-10
    download one-piece 1-2,5
    info one-piece
    search "One Piece Movie"
    list https://gogoanime.so/category/one-piece
    url https://gogoanime.so/one-piece-episode-1
"""
