from colorama import init, Fore, Back, Style

init()


def normal_info(*args, **kwargs):
    print(*args, **kwargs)


def bold_info(*args, **kwargs):
    print(Style.BRIGHT, end='')
    print(*args, **kwargs)
    print(Style.RESET_ALL, end='')


def success_info(*args, **kwargs):
    print(Fore.GREEN, end='')
    print(*args, **kwargs)
    print(Fore.RESET, end='')


def error_info(*args, **kwargs):
    print(Fore.RED, end='')
    print(*args, **kwargs)
    print(Fore.RESET, end='')


def warning_info(*args, **kwargs):
    print(Fore.YELLOW, end='')
    print(*args, **kwargs)
    print(Fore.RESET, end='')


def error_tag(*args, end='\n', **kwargs):
    print(Back.RED + Fore.BLACK, end='')
    print(*args, **kwargs, end='')
    print(Back.RESET + Fore.RESET, end=end)


def warning_tag(*args, end='\n', **kwargs):
    print(Back.YELLOW + Fore.BLACK, end='')
    print(*args, **kwargs, end='')
    print(Back.RESET + Fore.RESET, end=end)


def success_tag(*args, end='\n', **kwargs):
    print(Back.GREEN + Fore.BLACK, end='')
    print(*args, **kwargs, end='')
    print(Back.RESET + Fore.RESET, end=end)

def normal_tag(*args, end='\n', **kwargs):
    print(Back.WHITE + Fore.BLACK, end='')
    print(*args, **kwargs, end='')
    print(Back.RESET + Fore.RESET, end=end)


def prompt_val(prompt='', val='', output='normal', sep=": ", reverse=False):
    if reverse:
        globals()[f'{output}_tag'](val, end='')
        globals()[f'{output}_info'](sep+prompt)
    else:
        globals()[f'{output}_info'](prompt+sep, end='')
        globals()[f'{output}_tag'](val)
    
