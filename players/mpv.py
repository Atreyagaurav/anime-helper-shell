import time
import subprocess
import outputs

geometry = '300-0-20'

player_command = ''


def compile_command(flags='', fullscreen=False):
    global player_command
    com = [f'mpv {flags}']
    if geometry:
        com += [f'--geometry={geometry}']
    if fullscreen:
        com += ['--fs']
    player_command = com
    return com


def get_command(path, title=None, flags=''):
    com = " ".join(player_command)
    if title:
        com += f' --force-media-title={title}'
    com += f' "{path}"'
    return com


def play_media(link, title=None, fullscreen=False):
    while True:
        t1 = time.time()
        ret_val = subprocess.call(get_command(link, title),
                                  shell=True)
        if ret_val == 2:  # mpv error code
            outputs.error_info('Couldn\'t open the stream.')
            if input("retry?<Y/n>") == '':
                continue
            else:
                raise SystemExit
        return (time.time() - t1) > (5 * 60)
    # 5 minutes watchtime at least, otherwise consider it unwatched.
    # TODO: use direct communication with mpv to know if episode was
    # watched.



