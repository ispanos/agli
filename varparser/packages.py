from varparser.parser import get_variables
from typing import List, Optional, TypedDict


config = get_variables()


class RawPackages(list):
    """The list of 'packages' as they are read from the config files.

    List items: strs, dictionaries, or lists of strings or dictionaries.
    """
    pass


class Package(TypedDict):
    """
    package     Optional[str] Name of the package

    purpose     Optional[str] Some description

    manager     Optional[str] Package manager to handle the package

    repository  Optional[str] The repository to install the package from
    """
    package: Optional[str]
    purpose: Optional[str]
    manager: Optional[str]
    repository: Optional[str]


def is_pkg_dict(item: dict, valid_fields: tuple) -> bool:
    """Returns `true` if item is a valid package. Meaning that it does not have
    any unknown keys and contains either the key 'package', or the key
    'repository', in order to add a repository without associating with
    a specific package.

    Only accepts `dict`

    Args:
        item (dict): dict to be validated
        valid_fields (tuple): valid fields for package

    Returns:
        bool: True if item is package
    """
    is_package: bool = False

    if not isinstance(item, dict):
        return is_package

    for key, value in item.items():
        if key not in valid_fields:
            # Raises error because there is probably a typo in the config file
            raise Exception(
                f"Invalid configuration files: "
                f"key '{key}' is not valid for package '{item}'"
            )
        # TODO: If item is list, unpack it.
        # TODO: (not tested)
        if not isinstance(value, str) or not isinstance(value, list):
            raise Exception(
                f"Invalid package:\n '{item}'.\n"
                f"Type '{type(value)}' of '{key}':'{value}' must be string or list."
            )
        if key == 'package' and value:
            is_package = True

    is_repo: bool = False
    if 'repository' in item.keys():
        if item['repository']:
            is_repo = True

    return is_package or is_repo


def remove_empty_fields(item: dict):
    """Removes empty fields from `dict`.
    Useful for dumping dictionaries to stdout or file.
    """
    return {k: v for k, v in item.items() if v}


def parse_raw_packages(unparsed_packages: RawPackages) -> List[Package]:
    """Converts :class:`RawPackages` to a list of :class:`Package` items.

    Args:
        unparsed_packages (`RawPackages`): Packages as they are read
        from config file

    Raises:
        Exception: When items in `RawPackages` are not `list`, `str` or `dict`

    Returns:
        List[Package]: A list of Package items
    """

    if not unparsed_packages:
        return

    VALID_FIELDS = ('package', 'purpose', 'manager', 'repository')
    packages: List[Package] = list()

    for item in unparsed_packages:
        if not item:
            continue

        if isinstance(item, str):
            item: Package = {'package': item}
        elif is_pkg_dict(item, VALID_FIELDS):
            item = Package(item)
        else:
            raise Exception(
                f"Invalid item type: '{type(item)}' for item '{item}'."
            )
        packages.append(item)

    return packages


def parse_packages(unparsed: RawPackages) -> dict:
    if not unparsed:
        return None

    packages = parse_raw_packages(unparsed)

    new_format = {}

    for pkg in packages:
        # TODO: flatpak and pip now have 'manager' field
        if 'manager' in pkg.keys():
            manager = pkg['manager']
        else:
            manager = 'system'

        if not manager in new_format:
            new_format[manager] = {}

        manager_dict = new_format[manager]

        if 'package' in pkg:
            if 'packages' in manager_dict:
                manager_dict['packages'].append(pkg['package'])
            else:
                manager_dict['packages'] = [pkg['package']]

        if 'repository' in pkg:
            if 'repositories' in manager_dict:
                manager_dict['repositories'].append(pkg['repository'])
            else:
                manager_dict['repositories'] = [pkg['repository']]

        # TODO: Add prefix for ppa's or copr's ?
    return new_format
