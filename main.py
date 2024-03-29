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
import sys
import yaml
import json


def colorize_yaml(yaml_str):
    # Define ANSI escape codes for colors
    color_mapping = {
        'header': '\033[95m',  # Magenta
        'key': '\033[93m',     # Yellow
        'value': '\033[92m',   # Green
        'reset': '\033[0m'     # Reset color
    }

    colored_yaml = ""
    lines = yaml_str.split('\n')
    for line in lines:
        if not line:
            continue
        if line.strip().startswith('- '):
            # This line represents a list item
            colored_yaml += color_mapping['value'] + \
                line + color_mapping['reset'] + '\n'
        else:
            key, value = line.split(':', 1)
            key = key.strip()
            colored_yaml += color_mapping['key'] + \
                key + ':' + color_mapping['reset'] + ' '
            colored_yaml += color_mapping['value'] + \
                value.strip() + color_mapping['reset'] + '\n'

    return colored_yaml


def print_formatted_config(args, config):
    files_0 = None
    files_1 = None
    if config.pre_install_files:
        files_0 = [{'path': x.path, 'content': x.content}
                   for x in config.pre_install_files]

    if config.post_install_files:
        files_1 = [{'path': x.path, 'content': x.content}
                   for x in config.post_install_files]
    j_config = {
        # "First set of commands:"
        'commands_0': config.pre_install_commands,
        # "First set of files:"
        'files_0': files_0,
        # "Second set of files:"
        'files_1': files_1,
        # "Prerequisite packages need for the rest of the installation:"
        'packages_0': config.packages_prerequisite,
        # "Main list of packages:"
        'packages_1': config.packages,
        # "Second set of commands:"
        'commands_1': config.post_install_commands,
        # "Packages to be removed:"
        'remove': config.junk
    }

    j_config = {k: v for k, v in j_config.items() if v}

    if args.json:
        print(pretty_dict(j_config))
        return

    ymal_string = yaml.safe_dump(
        j_config, indent=2, default_flow_style=False, default_style='\"',
        width=1000)

    if args.color:
        print(((('-')*80)+'\n')*3)
        print("WARNING:")
        print("Colored output not working properly!")
        print(((('-')*80)+'\n')*3)

        try:
            parsed_yaml = yaml.safe_load(ymal_string)
            colorized_output = colorize_yaml(ymal_string)
            print(colorized_output)

        except yaml.YAMLError as e:
            print("Error parsing YAML:", e)
            sys.exit(1)

        print(((('-')*80)+'\n')*3)
        print("WARNING:")
        print("Colored output not working properly!")
        print(((('-')*80)+'\n')*3)

    else:
        print(ymal_string)


def main(args):

    if os.geteuid() == 0:
        print(
            "This script changes your users configurations thus it should not",
            "be run as root. You may need to enter your password multiple times."
        )
        sys.exit(1)

    if os.path.exists("log.txt"):
        os.remove("log.txt")
    config = get_variables(args.include, args.no_main)
    config = Configurations(config)
    package = PackageManager(config)

    print_formatted_config(args, config)

    if args.dry_run:
        return

    log_time()

    if config.dotfiles_repo is not None:
        clone_dotfiles(config.dotfiles_repo, config.current_user)

    if config.hostname is not None:
        change_hostname(config.hostname)

    # Added here to avoid installing unneeded dependencies.
    package.remove(config.junk)

    run_commands(config.pre_install_commands)

    create_files(config.pre_install_files)

    package.install(config.packages_prerequisite)

    package.install(config.packages)

    run_commands(config.post_install_commands)

    create_files(config.post_install_files)

    # Added here in case some junk got installed.
    package.remove(config.junk)

    log_time()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-i', '--include', nargs='+',
        help='Include specific yaml files with configurations.')

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without making actual changes.'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='When in dry-run mode, print configs in json format.'
    )

    parser.add_argument(
        '-c', '--color',
        action='store_true',
        help='When in dry-run mode, print configs with color.'
    )

    parser.add_argument(
        '--no-main',
        action='store_true',
        help='When used with -i/--include, ignore all main.yaml files.'
    )

    args = parser.parse_args()

    main(args)
