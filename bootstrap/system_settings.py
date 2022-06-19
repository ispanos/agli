from utils import execute_command, file_write, log_print


def change_hostname(name: str = None) -> None:
    """Changes the hostname of the computer

    Args:
        name (str): The new hostname
    """

    if not name:
        return

    hosts_content = (
        '#<ip-address>  <hostname.domain.org>    <hostname>\n'

        '127.0.0.1      localhost '
        'localhost.localdomain '
        'localhost4 '
        'localhost4.localdomain4\n'

        '::1            localhost '
        'localhost.localdomain '
        'localhost6 '

        'localhost6.localdomain6\n'
        f'127.0.1.1      {name}.localdomain  {name}\n')

    try:
        execute_command(f"hostnamectl set-hostname {name}", sudo=True)
    except Exception as e:
        log_print(e)
        log_print("Please reboot and try changing the hostname manually.")

    file_write(hosts_content, "/etc/hosts", use_sudo=True)
    file_write(name, "/etc/hostname", use_sudo=True)
