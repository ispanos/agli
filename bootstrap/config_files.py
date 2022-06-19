from typing import List, Union

from varparser.configurations import ConfigFile
from utils import file_write


def create_files(config_files: Union[List[ConfigFile], ConfigFile]) -> None:
    """Creates or overwrites files with the given ConfigFile's

    Args:
        config_files (Union[List[ConfigFile], ConfigFile]): List of ConfigFile or
        ConfigFile
    """
    if not config_files:
        return
    if isinstance(config_files, ConfigFile):
        config_files = [config_files]
    if not isinstance(config_files, list):
        raise Exception(f"Invalid argument: '{config_files}'")
    for file in config_files:
        file_write(file.content, file.path, use_sudo=file.use_sudo)
