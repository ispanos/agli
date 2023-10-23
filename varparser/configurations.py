import getpass
from typing import Dict, List

from varparser.packages import parse_packages
from varparser.parser import parse_os_release


class PackageManagerCommands():
    """Basic commands using by GenericPackageManager for performing
    rudimentary tasks, such as:
    - install [mandatory]
    - remove [madatory]
    - list installed packages [optional]
    - search for packages [optional]
    - upgrade [optional]
    - add new repositories [optional]
    """

    def __init__(self, commands: Dict[str, str]):
        self._commands = commands

        # commands_all = ('install', 'remove', 'upgrade',
        #                 'search', 'list_installed', 'add_extra_repo')

        commands_mandatory = ('install', 'remove')

        for command in commands_mandatory:
            if command in self._commands:
                continue
            raise Exception(
                f"invalid configuration files: '{command}' command is "
                "mandatory for 'package_managers' items"
            )
        self.install = self._commands['install']
        self.remove = self._commands['remove']

    @property
    def use_sudo(self) -> bool:
        if not 'use_sudo' in self._commands:
            return False
        if self._commands['use_sudo'] == True:
            return True
        return False

    # TODO: Raise exceptions before executing any commands
    @property
    def upgrade(self):
        if 'upgrade' not in self._commands:
            raise Exception(
                "invalid configuration: Feature 'upgrade' not present"
                "for this package manager."
            )
        return self.upgrade

    @property
    def add_extra_repo(self):
        if 'add_extra_repo' not in self._commands:
            raise Exception(
                "invalid configuration: Feature 'add_extra_repo' not present"
                "for this package manager."
            )
        return self._commands['add_extra_repo']

    @property
    def search(self):
        if 'search' not in self._commands:
            raise Exception(
                "invalid configuration: Feature 'search' not present"
                "for this package manager."
            )
        return self._commands['search']

    @property
    def list_installed(self):
        if 'list_installed' not in self._commands:
            raise Exception(
                "invalid configuration: Feature 'list_installed' not present"
                "for this package manager."
            )
        return self._commands['list_installed']


class Configurations:

    def __init__(self, config):
        self._config = config

        self.os_release = parse_os_release()
        self.current_user = getpass.getuser()

        self.packages = self._package_prep('packages')
        self.packages_prerequisite = self._package_prep('prerequisite_packages')
        self.junk = self._package_prep('remove')

        self.pm_commands = self._set_pm_commands()

        self.pre_install_commands = self.get_run_commands('pre_install')
        self.post_install_commands = self.get_run_commands('post_install')

        self.pre_install_files = self.get_files('pre_install')
        self.post_install_files = self.get_files('post_install')

        self.hostname = self.get_hostname()

        all_packages = (
            self.packages_prerequisite,
            self.packages,
            self.junk,
        )

        all_packages = [mgr for mgr in all_packages if mgr]

        needed_managers = list()
        for mgr in all_packages:
            needed_managers.extend([*mgr])

        needed_managers = list(set(needed_managers))

        for manager in needed_managers:
            if manager in self.pm_commands or manager == 'repositories':
                continue
            raise Exception(
                f"invalid configuration files: package manager '{manager}' "
                f"is required, but is not included in the configurations."
                f"If that doesn't look like a manager, maybe its a typo in "
            )

    # TODO: Add type for unparsed_packages
    def _package_prep(self, unparsed_packages) -> Dict[str, List[str]]:
        parsed = parse_packages(self._config[unparsed_packages])

        if not parsed:
            return None

        for manager in parsed.keys():
            for (values, items) in parsed[manager].items():
                parsed[manager][values] = sorted(list(set(items)))
        return parsed

    def _set_pm_commands(self) -> Dict[str, PackageManagerCommands]:
        if "package_managers" not in self._config:
            raise Exception(
                "invalid configuration files: Default configurations "
                "have been altered. Please restore 'defaults/' "
                "directory to it's original state and make changes "
                "only in 'vars/'."
            )

        package_managers = {}
        for (name, manager) in self._config["package_managers"].items():
            if name == self.os_id:
                name = 'system'
            package_managers[name] = PackageManagerCommands(manager)

        if 'system' not in package_managers:
            raise Exception(
                f"invalid configuration files: Package manager"
                f"for {self._config} was not found."
            )

        return package_managers

    @property
    def os_id(self):
        return self.os_release['ID']

    @property
    def flatpak_remotes(self):
        if 'flatpak_remotes' not in self._config:
            return None
        return self._config['flatpak_remotes']

    @property
    def dotfiles_repo(self):
        if 'dotfiles' not in self._config:
            return None
        return self._config['dotfiles']

    def get_hostname(self) -> str:
        if 'hostname' not in self._config:
            return None
        if not self._config['hostname']:
            return None
        if not isinstance(self._config['hostname'], str):
            raise Exception(
                f"Invalid config: hostname '{self._config['hostname']}' "
                f"is not supported ")
        return self._config['hostname']

    def get_run_commands(self, state):
        if not state in self._config:
            return None
        if not 'run' in self._config[state]:
            return None
        if not self._config[state]['run']:
            return None

        return [
            line.format(current_user=self.current_user)
            for line in self._config[state]['run']
        ]

    def get_files(self, state):
        if not state in self._config:
            return None
        if not 'files' in self._config[state]:
            return None
        if not self._config[state]['files']:
            return None
        return [
            ConfigFile(fd, self.current_user)
            for fd in self._config[state]['files']
        ]


class ConfigFile():

    def __init__(self, file_descriptor, current_user):
        self.current_user = current_user
        self._file_descriptor = file_descriptor
        self.path = self.get_var('path')
        self.content = self.get_var('content')
        self.use_sudo = self.get_sudo_flag()

    def get_var(self, var) -> str:
        if not var in self._file_descriptor:
            raise Exception(
                f"Invalid config: file - {self._file_descriptor} is not valid."
            )
        if not isinstance(self._file_descriptor[var], str):
            raise Exception(
                f"Invalid config: for file - {self._file_descriptor} is not valid. "
                f"'{var}' must be a string."
            )
        return self._file_descriptor[var].format(current_user=self.current_user)

    def get_sudo_flag(self) -> bool:
        if 'sudo' not in self._file_descriptor:
            return True
        if not isinstance(self._file_descriptor['sudo'], bool):
            raise Exception(
                f"Invalid config: for file - {self._file_descriptor} is not valid. "
                f"'sudo' must be boolean."
            )
        return self._file_descriptor['sudo']
