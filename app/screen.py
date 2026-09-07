"""
we can use a Linux screen rather than Docker
"""

from paths import resource_path
from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

from vps import establish_ssh_connection, run_remote

CONFIG_PATH = resource_path("deployctl.conf")

def load_config():
    # load the config
    try:
        config = ConfigFactory.parse_file(str(CONFIG_PATH))
    except FileNotFoundError:
        # no config file with path provided
        print(f"Configuration file not found at {CONFIG_PATH}. Please create the configuration file.")
        return None

    try:
        project_name = config.get('core.project_name')
        setup_command = config.get('core.setup_command')
        start_command = config.get('core.start_command')
        path_for_project = config.get('core.path_for_project')
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return project_name, setup_command, start_command, path_for_project

def create_screen():
    loaded = load_config()
    if loaded is None:
        return False
    project_name, setup_command, start_command, path_for_project = loaded

    project_path = f"{path_for_project.rstrip('/')}/{project_name}"

    client = establish_ssh_connection()
    if not client:
        return False

    if not run_remote(client, f'bash -c "mkdir -p {project_path}"'):
        print("An error occurred setting up the path for the project")
        return False

    if not run_remote(client, f'bash -c "cd {project_path} && {setup_command}"'):
        print("An error occurred setting up the environment")
        return False

    screen_cmd = f'screen -dmS {project_name} bash -c "cd {project_path} && {start_command}"'
    if not run_remote(client, screen_cmd):
        print("An error occurred starting and running the screen")
        return False

    return True

if __name__ == "__main__":
    screen = create_screen()
    if screen:
        print("A screen has been created")