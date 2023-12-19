import copy
import functools
from typing import List, Tuple, Union
import yaml
import os

from varparser.constants import CONFIG_FILES, CONFIG_DIRS, VALID_EXTENSIONS


def pop_include_files(config: dict) -> Tuple[dict, list]:

    copy.deepcopy(config)

    paths = config.pop('include')

    if isinstance(paths, str):
        [paths]

    for file in paths:
        _, file_extension = os.path.splitext(file)
        if not any(file_extension in ext for ext in VALID_EXTENSIONS):
            raise Exception(
                f"'{file_extension}' is not a valid file extension for file: '{file}'.")

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


def get_variables(included_files_arg: List[str] = None, default_only=False) -> dict:

    # Load and merge the default and main config files

    top_config = list(CONFIG_FILES)

    if default_only:
        top_config = [CONFIG_FILES[0]]

    if included_files_arg:
        top_config.extend(find_yaml_files(included_files_arg))

    configs_list = [load_config(path) for path in top_config]
    configs_list = [config for config in configs_list if config]  # TODO: Why?
    user_configs = functools.reduce(_dict_update, configs_list)

    included_files = []
    configs = user_configs

    if 'include' in user_configs:
        if user_configs['include']:
            configs, included_files = pop_include_files(user_configs)

    extra_files = []

    if included_files:
        extra_files.extend(included_files)

    if not extra_files:
        return configs

    # TODO: Check for Included files inside of included files
    # TODO: But how many layers in?
    extra_configs_list = [load_config(path) for path in extra_files]

    extra_configs_list = [config for config in extra_configs_list if config]

    final = [configs]
    final.extend(extra_configs_list)
    final = functools.reduce(_dict_update, final)

    return final


# TODO: Refactor
def find_yaml_files(
        file_names: List[str],
        config_dirs: List[str] = None,
        valid_ext: List[str] = None):
    """
    Find configuration files with the specified names in the given directories or default directories.

    Args:
        file_names (list of str): A list of file names (without extensions) to search for.
        config_dirs (list of str, optional): A list of directory paths to search for the configuration files.
            If not provided, it uses default configuration directories defined in CONFIG_DIRS.
        valid_ext A list of 'valid' extensions for the files it searches. Defaults to VALID_EXTENSIONS constant.

    Returns:
        list of str: A list of relative paths to the found YAML configuration files.

    Raises:
        ValueError: If duplicate file names are found within the specified or default directories.

    Notes:
        - It raises an exception if duplicate file names are detected -- use full relative paths to avoid error.
        - You can customize the default configuration directories by modifying the CONFIG_DIRS constant.
        - The 'config_dirs' argument allows you to specify custom directories for the search.

    Example:
        To find 'myconfig' in custom directories:
        >>> custom_dirs = ['/path/to/custom/dir1', '/path/to/custom/dir2']
        >>> yaml_files = find_yaml_files(['myconfig'], custom_dirs)

        To find 'myconfig' in default directories:
        >>> yaml_files = find_yaml_files(['myconfig'])
    """
    result = []
    seen = set()  # To keep track of encountered file names
    if not config_dirs:
        config_dirs = CONFIG_DIRS

    if not valid_ext:
        valid_ext = VALID_EXTENSIONS

    os_release = parse_os_release()
    os_id = os_release["ID"]
    config_dirs = [path.format(os_id=os_id) for path in config_dirs]

    for file_name in file_names:
        for config_dir in config_dirs:
            directory_path = os.path.dirname(file_name)
            if directory_path == config_dir:
                _, ext = os.path.splitext(file_name)
                if ext not in valid_ext:
                    raise ValueError(f"Invalid extensions: {file_name}")
                if not os.path.exists(file_name):
                    raise ValueError(f"File not found: {file_name}")
                # Not added in seen if given path includes dir.
                result.append(file_name)
                continue

            yaml_file_path = None

            # Check both possible extensions: .yml and .yaml
            for ext in valid_ext:
                potential_path = os.path.join(config_dir, f"{file_name}{ext}")
                # Check if the file exists
                if os.path.exists(potential_path):
                    if file_name in seen:
                        raise ValueError('\n'.join([
                            f"Duplicate file name found: '{file_name}'",
                            " - Avoid using both 'yml' and 'yaml' as a file extensions",
                            f" - Avoid using the same file names for configs in vars/ and /vars/{os_id}",
                            f" - Use the whole relative path if you need to have files with the same name",
                        ]))

                    seen.add(file_name)
                    yaml_file_path = potential_path

            if yaml_file_path:
                result.append(yaml_file_path)

    for file_name in file_names:
        if not any(file_name in i for i in result):
            raise ValueError(f"File not found: {file_name}")

    return result
