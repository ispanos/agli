from subprocess import CompletedProcess
from typing import List, Union

from bootstrap.errors import Sorry
from utils import execute_command
from varparser.configurations import Configurations, PackageManagerCommands


class PackageManager():
    def __init__(self, config: Configurations) -> None:
        self.config = config
        self._managers = {}

    def _get_package_manager(self, alias: str) -> 'GenericPackageManager':
        if alias not in self._managers:
            self._managers[alias] = get_package_manager(self.config, alias)
        return self._managers[alias]

    def install(self, packages):
        if not packages:
            return
        for pm_alias, pm_packages in packages.items():
            pm = self._get_package_manager(pm_alias)
            if 'repositories' in pm_packages:
                pm.add_extra_repo(pm_packages['repositories'])
            if 'packages' in pm_packages:
                pm.install(pm_packages['packages'])

    def remove(self, packages):
        if not packages:
            return
        for pm_alias, pm_packages in packages.items():
            pm = self._get_package_manager(pm_alias)
            if 'packages' in pm_packages:
                pm.remove(pm_packages['packages'])

    def upgrade(self):
        raise Sorry()

    def list_installed(self, alias: str):
        pm = self._get_package_manager(alias)
        return pm.list_installed()

    def add_extra_repo(self, repositories):
        if not repositories:
            return
        for pm_alias, pm_repositories in repositories.items():
            pm = self._get_package_manager(pm_alias)
            pm.add_extra_repo(pm_repositories)

    def search(self):
        raise Sorry()

    # TODO: Remove repo?


class GenericPackageManager():
    def __init__(
            self,
            pm_config: PackageManagerCommands
    ):

        self._pm_config = pm_config

    def install(self, packages: Union[list, str]) -> CompletedProcess[str]:
        if not packages:
            return

        if isinstance(packages, list):
            packages = " ".join(packages)

        return execute_command(
            f"{self._pm_config.install} {packages}",
            sudo=self._pm_config.use_sudo
        )

    def remove(self, packages: Union[List[str], str]) -> CompletedProcess[str]:
        if isinstance(packages, list):
            packages = " ".join(packages)

        return execute_command(
            f"{self._pm_config.remove} {packages}",
            sudo=self._pm_config.use_sudo
        )

    def _add_extra_repo(self, repository: str) -> CompletedProcess[str]:
        return execute_command(
            f"{self._pm_config.add_extra_repo} {repository}",
            sudo=self._pm_config.use_sudo
        )

    def add_extra_repo(self, repositories: Union[str, List[str]]) -> None:
        if not isinstance(repositories, list):
            repositories = [repositories]

        for repository in repositories:
            self._add_extra_repo(repository)

    def list_installed(self) -> str:
        result = execute_command(self._pm_config.list_installed, _print=False)
        return result.stdout

    def upgrade(self) -> CompletedProcess[str]:
        return execute_command(self._pm_config.upgrade)

    def search(self, package) -> str:
        return execute_command(f"{self._pm_config.search} {package}").stdout


def get_package_manager(config: Configurations, alias: str) -> GenericPackageManager:
    pkg_cmds: PackageManagerCommands = config.pm_commands[alias]
    return GenericPackageManager(pkg_cmds)
