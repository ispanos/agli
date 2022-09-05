#!/usr/bin/env python

import argparse
import os

from bootstrap.config_files import create_files
from bootstrap.package_manager import PackageManager
from bootstrap.system_settings import change_hostname
from bootstrap.user_settings import clone_dotfiles
from utils import log_print, log_time, pretty_dict
from varparser.command_parser import run_commands
from varparser.configurations import Configurations
from varparser.parser import get_variables


def main():

    if os.geteuid() == 0:
        print(
            "This script changes your users configurations thus it should not",
            "be run as root. You may need to enter your password multiple times."
        )
        exit(1)

    if os.path.exists("log.txt"):
        os.remove("log.txt")

    log_time()

    config = get_variables()
    log_print(pretty_dict(config))

    config = Configurations(config)
    package = PackageManager(config)

    run_commands(config.pre_install_commands)

    create_files(config.pre_install_files)

    package.install(config.packages_prerequisite)

    package.install(config.packages)

    run_commands(config.post_install_commands)

    create_files(config.post_install_files)

    package.remove(config.junk)

    change_hostname(config.hostname)

    clone_dotfiles(config.current_user, config.dotfiles_repo)

    fresh_installed = f"/home/{config.current_user}/.local/fresh_pack_list"
    if not os.path.exists(fresh_installed):
        installed = package.list_installed('system')
        log_print(installed, _print=False, log_file=fresh_installed)

    log_time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # parser.add_argument('-x', '--no-main', help='')
    # parser.add_argument('-i', '--include', help='')
    # parser.add_argument('command', help='You can use the following commands: search, get, set')
    # parser.add_argument('-c', '--client', help='IP address of the client device')
    # parser.add_argument('params', nargs='*', default=None, type=str)


    main()
