CONFIG_FILES = (
    'defaults/main.yaml',
    'vars/main.yaml',
    'vars/{os_id}/main.yaml',
)

CONFIG_DIRS = (
    'defaults',
    'vars',
    'vars/{os_id}',
)

VALID_EXTENSIONS = ('.yml', '.yaml')
