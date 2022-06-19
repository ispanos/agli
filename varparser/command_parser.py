

from utils import line_prepender, list_to_tmpfile, make_executable, run_script


def run_commands(commands):
    if not commands:
        return

    path = list_to_tmpfile(commands)

    # Add shebang
    line_prepender(path, '#!/bin/sh')

    make_executable(path)
    result = run_script(path)
    if not result == 0:
        raise Exception('Something went wrong!.')
