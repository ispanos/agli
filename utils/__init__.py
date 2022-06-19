import difflib
import errno
import io
import os
import random
import selectors
import string
import subprocess
import getpass
import copy
from typing import List, TypeAlias, Union
import json
from datetime import datetime


LOG_FILE = "log.txt"


def log_time():
    print(datetime.now(), "\n")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{datetime.now()} \n")


def my_log(s: str, log_file: str = None):
    if not log_file:
        log_file = LOG_FILE
    with open(log_file, "a") as lf:
        lf.write(f"{s} \n")


def log_print(
        *args: Union[str, bytes],
        _print: bool = True,
        log_file: str = None
) -> None:
    """Prints arguments to terminal and adds it to log.txt file."""
    for s in args:
        if isinstance(s, bytes):
            s = s.decode("UTF-8")
        my_log(s, log_file=log_file)
        if _print:
            print(s)


def pretty_dict(d: dict) -> str:
    """Converts dictionary to a formatted string.

    Args:
        d (dict): Dictionary

    Returns:
        str: Formatted string
    """
    return json.dumps(d, sort_keys=False, indent=4)


def execute_command(
        command,
        sudo: bool = False,
        _print: bool = True,
        command_input: str = None,
        check: bool = True,
):
    """Credits to nawatts/capture-and-print-subprocess-output.py"""

    if sudo:
        command_input = get_password()
        command = f"sudo --stdin {command}"

    """Start subprocess
    bufsize = 1 means output is line buffered
    universal_newlines = True is required for line buffering"""
    process = subprocess.Popen(
        command,
        bufsize=1,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
        universal_newlines=True,
        text=True,
    )

    if command_input:
        process.stdin.write(command_input)

    # Create callback function for process output
    buf = io.StringIO()
    log_print(command)

    def handle_output(stream, mask):
        # Because the process' output is line buffered, there's only ever one
        # line to read when this function is called
        line = stream.readline()
        buf.write(copy.copy(line))
        log_print(line)

    # Register callback for an "available for read" event from subprocess' stdout stream
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, handle_output)

    # Loop until subprocess is terminated
    while process.poll() is None:
        # Wait for events and handle them with their registered callbacks
        events = selector.select()
        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

    # Get process return code
    return_code = process.wait()
    selector.close()

    output = buf.getvalue()
    buf.close()

    if return_code != 0 and check:
        raise Exception(
            f"Command: '{command}' failed with {return_code}."
        )

    setattr(process, "stdout", output)
    setattr(process, "returncode", return_code)
    return process


def sudo_prompt():
    password = None
    try:
        for i in range(4):
            if i > 1:
                password = getpass.getpass(f"[sudo] password for {getpass.getuser()}: ")
            command = "sudo -S echo 'Check if sudo is unlocked.'"
            result = subprocess.run(
                command,
                input=password,
                text=True,
                shell=True,
                check=False,
            )
            if result.returncode == 0:
                return password
            print("Password error")
    except Exception as err:
        raise Exception("Failed to retrieve sudo password") from err


def get_password():
    if not hasattr(get_password, "__password"):
        password = sudo_prompt()
        # Uncomment to always ask for password
        # if not password:
        # raise Exception("Failed to retrieve sudo password")
        setattr(get_password, "__password", password)
        return password
    return getattr(get_password, "__password")


def command_v(command: str) -> bool:
    """Checks if a command exists using 'command -v {arg}'"""
    return subprocess.run(
        f"command -v {command}".split(),
        stdout=subprocess.DEVNULL
    ).returncode == 0


def diff_files(file_a: str, file_b: str) -> str:
    with open(file_a) as file_1:
        file_a_text = file_1.readlines()

    with open(file_b) as file_2:
        file_b_text = file_2.readlines()

    diff = []

    for line in difflib.unified_diff(
            file_a_text, file_b_text, fromfile=file_a,
            tofile=file_b, lineterm=''):
        diff.append(line)

    return "\n".join(diff)


def get_rand_tmp_file_name() -> str:
    """TODO replace
    Returns a random file name in /tmp"""
    letters = string.ascii_lowercase
    rand_name = (''.join(random.choice(letters) for i in range(15)))

    return f"/tmp/{rand_name}"


def sudo_write_file(content: str, perm_location: str) -> None:
    """Writes file in /tmp and moves it to another location using sudo.
    Allows user to write to files that python doesn't have permission
    to write to.

    Args:
        content (str): What will be in the file
        perm_location (str): The file to write to.
    """
    tmp_location = get_rand_tmp_file_name()

    with open(tmp_location, 'w') as file:
        file.write(content)

    exists = os.path.exists(perm_location)

    if exists:
        log_print(f"\n\n\nWriting in file '{perm_location}': \n{content}\n\n\n")
        log_print(diff_files(perm_location, tmp_location))
    else:
        log_print(f"\n\n\nOverwriting file '{perm_location}' with: \n{content}\n\n\n")

    execute_command(f"mv {tmp_location} '{perm_location}'", sudo=True)


def file_write(content: str, path: str, use_sudo: bool = None) -> None:
    if use_sudo:
        sudo_write_file(content, path)
    else:
        log_print(f"\n\n\nWritting in file '{path}': \n{content}\n\n\n")
        log_print(content, _print=False, log_file=path)


def list_to_tmpfile(commands: List[str]) -> str:
    """Writes list of strings to file. Each item is a new line

    Args:
        commands (List[str]): List of strings

    Returns:
        str: Temporary file path
    """
    path = get_rand_tmp_file_name()
    with open(path, 'w') as fp:
        for item in commands:
            if not isinstance(item, str):
                raise Exception(
                    f"Path '{item}' must be a string, not '{type(item)}'"
                )
            fp.write("%s\n" % item)

    return path


def line_prepender(filename, line):
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content)


def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)


def run_script(path: str):
    return subprocess.call(path)


StrOrBytesPath: TypeAlias = str | bytes | os.PathLike[str] | os.PathLike[bytes]


def force_symlink(
        src: StrOrBytesPath,
        dst: StrOrBytesPath,
        target_is_directory: bool = False,
) -> None:
    try:
        os.symlink(src, dst, target_is_directory)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(dst)
            os.symlink(src, dst)
