"""
rolls back to the previously deployed version.

- docker mode: container.py tags the existing :latest as :previous right
  before building a new image, so rollback stops the current container and
  runs the :previous image instead.
- linux mode: cli.py's sync_files() backs up the previous synced project
  directory as <path>.previous before overwriting it with new files, so
  rollback restores that directory and restarts the screen session from it.

either way, there must have been a prior successful deploy for rollback to
have something to fall back to — a first-ever deploy has nothing to roll
back to, and this fails cleanly in that case rather than guessing.
"""

from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

from app.paths import resource_path
from app.vps import establish_ssh_connection, run_remote


def load_config():
    # load the config
    config_path = resource_path("deployctl.conf")
    try:
        config = ConfigFactory.parse_file(str(config_path))
    except FileNotFoundError:
        # no config file with path provided
        print(f"Configuration file not found at {config_path}. Please create the configuration file.")
        return None

    try:
        project_name = config.get('core.project_name')
        how_to_run = config.get('core.how_to_run')
        port = config.get('core.port')
        path_for_project = config.get('core.path_for_project')
        start_command = config.get('core.start_command')
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return project_name, how_to_run, port, path_for_project, start_command


def _rollback_docker(client, project_name, port):
    previous_tag = f"{project_name}:previous"

    if not run_remote(client, f'docker image inspect {previous_tag}'):
        print(f"No previous image found ({previous_tag}) — nothing to roll back to.")
        return False

    # ignore failure — there may not be a running container to remove
    run_remote(client, f'bash -c "docker rm -f {project_name} || true"')

    run_cmd = f'bash -c "docker run -d --name {project_name} -p {port}:{port} {previous_tag}"'
    if not run_remote(client, run_cmd):
        print("An error occurred starting the previous container")
        return False

    print(f"Rolled back {project_name} to {previous_tag}")
    return True


def _rollback_linux(client, project_name, path_for_project, start_command):
    if path_for_project.startswith("~"):
        _stdin, stdout, _stderr = client.exec_command("echo $HOME")
        remote_home = stdout.read().decode().strip()
        path_for_project = remote_home + path_for_project[1:]

    project_path = f"{path_for_project.rstrip('/')}/{project_name}"
    previous_path = f"{project_path}.previous"

    if not run_remote(client, f'test -d {previous_path}'):
        print(f"No previous version found at {previous_path} — nothing to roll back to.")
        return False

    # stop the current screen session — ignore failure if it's not running
    run_remote(client, f'bash -c "screen -S {project_name} -X quit || true"')

    swap_cmd = f'bash -c "rm -rf {project_path} && mv {previous_path} {project_path}"'
    if not run_remote(client, swap_cmd):
        print("An error occurred restoring the previous version")
        return False

    screen_cmd = f'screen -dmS {project_name} bash -c "cd {project_path} && {start_command}"'
    if not run_remote(client, screen_cmd):
        print("An error occurred restarting the previous version")
        return False

    print(f"Rolled back {project_name} to the previous synced version")
    return True


def rollback():
    loaded = load_config()
    if loaded is None:
        return False
    project_name, how_to_run, port, path_for_project, start_command = loaded

    client = establish_ssh_connection()
    if not client:
        return False

    if how_to_run == "docker":
        return _rollback_docker(client, project_name, port)
    elif how_to_run == "linux":
        return _rollback_linux(client, project_name, path_for_project, start_command)
    else:
        print(f"Unknown core.how_to_run value: '{how_to_run}'. Must be 'docker' or 'linux'.")
        return False


if __name__ == "__main__":
    import sys
    sys.exit(0 if rollback() else 1)
