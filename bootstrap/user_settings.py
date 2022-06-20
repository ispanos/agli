import getpass
import os
import tempfile

from utils import execute_command, command_v, force_symlink, log_print


def clone_dotfiles(user: str = None, repo: str = None) -> None:
    """Clones dotfiles and places the in the user's home, but changes the name
    of --git-dir to ".cfg", to avoid nested git repositories in the home 
    directory. To make changes to the repo in the future, use the alias
    suggested in the following article:
    https://www.atlassian.com/git/tutorials/dotfiles

    alias config='/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME'


    Args:
        repo (str): Link to dotfiles git repository.
        user (str): The name of the user for whom the dotfiles are for.
    """

    if not command_v('git'):
        log_print("Cloning dotfiles requires git.")
        return

    if not repo:
        log_print("Skipping; dotfiles' repository was not defined.")
        return

    if not user:
        user = getpass.getuser()

    dir = tempfile.mkdtemp()
    dot = f"git --git-dir=\"{dir}/.cfg/\" --work-tree=\"{dir}\""

    execute_command(f"chown -R {user} {dir}", sudo=True)
    with open(f"{dir}/.gitignore", 'w') as f:
        f.write(".cfg")

    execute_command(f"git clone -q --bare {repo} {dir}/.cfg")

    execute_command(f"{dot} checkout")
    execute_command(f"{dot} config --local status.showUntrackedFiles no")

    os.remove(f"{dir}/.gitignore")

    execute_command(f"cp -rfT {dir}/ /home/{user}/")
    force_symlink(f"/home/{user}/.profile", f"/home/{user}/.zprofile")
