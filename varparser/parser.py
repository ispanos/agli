import copy
import functools
from typing import List, Tuple, Union
import yaml
import os

from varparser.constants import CONFIG_FILES


def pop_include_files(config: dict) -> Tuple[dict, list]:

    copy.deepcopy(config)

    paths = config.pop('include')

    if isinstance(paths, str):
        [paths]

    for file in paths:
        _, file_extension = os.path.splitext(file)
        if not file_extension == '.yaml' or file_extension == '.yml':
            raise Exception(f"'{file_extension}' is not a valid file extension.")

    return config, paths


def _dict_update(existing_vars: dict, new_vars: dict) -> dict:
    """Merges two dictionaries into one, extending all lists and keys in nested
    dictionaries. All other types (strings, integers) are replaced with the
    new values.
    """
    merged = copy.deepcopy(existing_vars)
    for (key, value) in new_vars.items():
        if value is None:
            continue

        if isinstance(value, dict):
            if key not in merged:
                merged[key] = dict()
            merged[key] = _dict_update(merged[key], value)

        elif isinstance(value, list):
            if key not in merged:
                merged[key] = list()
            if not merged[key]:
                merged[key] = new_vars[key]
            else:
                merged[key].extend(new_vars[key])

        else:
            merged[key] = new_vars[key]

    return merged


def load_config(path: str) -> dict:
    os_release = parse_os_release()
    path = path.format(
        os_id=os_release["ID"]
    )
    if not os.path.exists(path):
        return None
    with open(path, "r") as configfile:
        return yaml.load(configfile, Loader=yaml.FullLoader)


def parse_os_release() -> dict:
    """Returns information about the os release (distro, version, etc.).

    Returns:
        dict: Contains every line of /etc/os-release
    """
    with open("/etc/os-release") as f:
        os_release_info = {}
        for line in f:
            k, v = line.rstrip().split("=")
            os_release_info[k] = v.strip('"')
        return os_release_info


def get_base_variables():
    configs_list = [load_config(path) for path in CONFIG_FILES]
    configs_list = [config for config in configs_list if config]

    user_configs = functools.reduce(_dict_update, configs_list)

    if not 'include' in user_configs:
        return user_configs, None

    if not user_configs['include']:
        return user_configs, None

    return pop_include_files(user_configs)


def get_variables(paths: Union[List[str], str] = None) -> dict:

    configs, included_files = get_base_variables()

    if isinstance(paths, str):
        paths = [paths]

    extra_files = []

    if paths:
        extra_files.extend(paths)

    if included_files:
        extra_files.extend(included_files)

    if not extra_files:
        return configs

    extra_configs_list = [load_config(path) for path in extra_files]

    extra_configs_list = [config for config in extra_configs_list if config]

    final = [configs]
    final.extend(extra_configs_list)
    final = functools.reduce(_dict_update, final)

    return final
