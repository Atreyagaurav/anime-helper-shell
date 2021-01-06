"""Prototype module for debugging.

Got bored of sending line to python REPL and importing everything everytime.

So here goes the debug REPL just like Python REPL.
"""
import re
import cmd
import traceback
import itertools
import importlib

import gogoanime
import commands
import config
import utils
import notification

shell_commands = {
    "gogoanime": gogoanime,
    "commands": commands,
    "config": config,
    "utils": utils,
    "notification": notification
}


class DebugShell(cmd.Cmd):
    identchars = cmd.IDENTCHARS + '.'
    prompt = "\x1b[41mDEBUG\x1b[0m $"

    def __init__(self, ggshell, *args, **kwargs):
        super(DebugShell, self).__init__(*args, **kwargs)
        self.parent = ggshell

    def do_shell(self, inp):
        try:
            self.parent.onecmd(inp)
        except Exception as e:
            print(e)

    def import_mod(self, inp):
        """Import python modules.
Supported commands:
 - import module
 - import module as alias
 - from module import something

doesn't work if there is . in name but no alias.
like: import os.path
but import os.path as path works.
"""
        m = re.match(r'^import ([\w.]+)\s*$', inp)
        if m:
            shell_commands[m.group(1)] = importlib.import_module(m.group(1))
            return
        m = re.match(r'^import ([\w.]+) +as +(\w+)\s*$', inp)
        if m:
            shell_commands[m.group(2)] = importlib.import_module(m.group(1))
            return
        m = re.match(r'^from ([\w.]+) +import +(\w+)\s*$', inp)
        if m:
            shell_commands[m.group(2)] = getattr(
                importlib.import_module(m.group(1)), m.group(2))

    def default(self, inp):
        if 'import' in inp:
            return self.import_mod(inp)
        try:
            print(eval(inp, {}, shell_commands))
        except Exception as e:
            print(e)

    def completedefault(self, text, line, *args):
        # TODO : it's very incomplete, it's just a prototype
        if len(line)>0 and line[0]=='!':
            if ' ' in line:
                lls = line.split(' ', 2)
                try:
                    compfunc = getattr(self.parent, 'complete_' + lls[0])
                except AttributeError:
                    compfunc = self.parent.completedefault
                return compfunc(text, line[1:], *args)
            else:
                return self.parent.completenames(text, line[1:], *args)
        if '.' in text:
            texts = text.split('.', 1)
            if texts[0] in shell_commands:
                possible = dir(shell_commands[texts[0]])
                match = filter(lambda a: a.startswith(texts[1]), possible)
                completion = map(lambda m: f'{texts[0]}.{m}', match)
                return list(completion)
            else:
                return []

        commands = filter(lambda a: 'Error' not in a and not a.startswith('_'),
                          dir(__builtins__))
        possible = itertools.chain(shell_commands, commands)
        match = filter(lambda a: a.startswith(text), possible)
        return list(match)

    completenames = completedefault

    def do_exit(self, inp):
        return True

    def do_traceback(self, inp):
        print(traceback.print_exc())
