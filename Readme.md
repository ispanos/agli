# Ptinopedila (The birds of Mercury)

## Description

A turn-key solution to configure a Linux system. Ptinopedila uses configuration files written in `yaml` to adjust and expand the capabilities of the script.

For now, only basic functionality is scripted in python, but given enough demand from other users, or me, more can be added. However, I do not plan to re-write Ansible, I just want a quick way to configure a new system in a pinch.

### Current functionality

- Install/Remove packages
- Add repositories
- List installed packages
- Search for packages using a package manager (I don't know why)
- Run bash commands/scripts
- Create text files (as user or as root)
- Change device's hostname
- Clone a "dotfiles" repository from GitHub
- Work for many distributions/ package managers, without having to code

## Customization

You can find all available keywords in `defaults/main.yaml`. Instead of editing the defaults directly, you should create a `vars/main.yaml` file with your configurations. For examples, you can have a look in the `templates/ispanos/` directory to see how I structure my configurations.

## Syntax

```yaml
dotfiles:
```

When given a link (string) to a [dotfiles](https://github.com/ispanos/dotfiles) repository (see link), it clones the repository and places the files in your home directory, overwriting existing files. Instead of the standard `.git/` directory, it uses `.cfg/`, to avoid issues with nested git directories.
You can delete the `.cfg/` directory or use the following alias to commit and push changes to your dotfiles repository.

`dot="/usr/bin/git --git-dir=$HOME/.cfg/ --work-tree=$HOME"`

```yaml
hostname:
```

Runs `sudo hostnamectl set-hostname {hostname}` to change the hostname.

```yaml
package_managers:
```

In order to support more distributions, without having to code a different package manager for each distro, this script has a generic package manager implementation and some essential commands can be added as a dictionary (as seen in `defaults/main.yaml`).

Make sure to name any new *system* `package_manager` dictionaries with the `ID` of your distro as it is in `/etc/os-release`. Also, don't forget to set `use_sudo: true`, when the commands require sudo privileges. (AUR helpers, flatpak and pip should be run as your user.)

```yaml
packages:
```

A list of packages\* (string or dictionary). When the package is a simple string, it is assumed that the *system*'s package manager will be used. The package can also be written as a dictionary, with the keys `package`, `repository`, `manager`.

`package` is the name of the package.

The `repository` field can be used for flatpak remotes, PPAs, DNF coprs, DNF repositories etc. It is handled by the `add_extra_repo:` command in `package_managers`.

For example:

In order to install `R-CoprManager` from the copr `iucar/cran` (on Fedora), the following configuration is needed:

```yaml
packages:
  - package: R-CoprManager
      manager: system # Can be omitted.
      repository: iucar/cran
package_managers: 
fedora:
  install: dnf install -y
  remove: dnf remove -y
  add_extra_repo: dnf copr enable -y
  use_sudo: true
```

The `manager` field specifies which of the `package_managers` will be used to handle the package/repository. Omitting this field is the same as `manager: system`, where `system` is an alias for all distributions' package managers.

The field 'purpose' is a placeholder - comment. Any other fields raise an Exception.

i.e.

```yaml
- package: radian
  manager: pip
  # installs radian using pip

- package: io.dbeaver.DBeaverCommunity
  manager: flatpak
  # installs io.dbeaver.DBeaverCommunity from flatpak
  # (if the flathub repo has been added)
```

```yaml
package_managers:
  flatpak:
    install: flatpak install -y --system flathub
    remove: flatpak uninstall -y
    add_extra_repo: flatpak remote-add --if-not-exists
packages:
  - manager: flatpak
    repository: flathub https://flathub.org/repo/flathub.flatpakrepo
```

\* The `package` field can be omitted for special cases, like adding the flathub remote to flatpak.

```yaml
prerequisite_packages:
```

Is a list with the same syntax as `packages:` and can be used to install some packages before the rest. In `defaults/main.yaml` you can see that I use it to install flatpak and the 'flathub' remote. This way, I can be sure that packages from flathub will be installed without an issue. You can also see in my `vars` *template* that I use it to install `dnf` repositories (such as RPM Fusion).

```yaml
pre_install:
post_install:
```

These are dictionaries that include a `files` list and a `run` list. They are run before and after installing `packages:` respectively.

`run` is a list of commands that will be concatenated into a single file and will be executed as a bash script. These lists are basically a way to expand my script with your existing bash scripts (since commands can also be executable files).

`files` is a list of dictionaries that have a `path:` and a `content:`. Use it with caution, because it overrides existing files.

**WARNING**: There is also a `use_sudo` field, but do not use it, useless you test it in a VM first. It will change file permissions/ownership and may cause issues to your system.

```yaml
remove:
```

A list of packages to be removed (same syntax as `packages`).

```yaml
include:
```

Possibly one of the most useful features, is the ability to break your configurations down into multiple files and `include` them by adding them in the `include` list, either as list items or as strings. `include` does not work recursively, so, only files included in the `main.yaml` files will be merged. The way the included files are merged is the same as the way `vars` merge with the `defaults`.

My `defaults` are merged with `vars` by overriding all string values, and extending lists. This is also applied for strings and lists in dictionaries. If you want to remove flatpak and the flathub remote from your configuration, you will have to remove them from the `defaults/main.yaml` file.

## To-do

- Create a CLI interface.
  - Add flag to specify the `vars` directory location.
- Add tests

If you want to contribute to this repository, maybe you could help me write some tests. Docker cannot be used to test everything this script does.
