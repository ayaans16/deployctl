"""
docker logic

builds and runs the project's Docker image directly on the VPS, over the
same SSH connection used elsewhere (nginx, ssl, screen) — rather than
building locally and needing a separate way to ship the image to the VPS
afterward (a registry push/pull, or a saved tarball).

prerequisite: the synced project directory must contain a Dockerfile !!!!
"""

from app.paths import resource_path
from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

from app.vps import establish_ssh_connection, run_remote

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
        path_for_project = config.get('core.path_for_project')
        port = config.get('core.port')
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return project_name, path_for_project, port

def run_container():
    loaded = load_config()
    if loaded is None:
        return False
    project_name, path_for_project, port = loaded
    project_path = f"{path_for_project.rstrip('/')}/{project_name}"

    client = establish_ssh_connection()
    if not client:
        return False

    # assumption is a Dockerfile already exists in the synced project directory
    build_cmd = f'bash -c "cd {project_path} && docker build -t {project_name}:latest ."'
    if not run_remote(client, build_cmd):
        print("An error occurred building the Docker image")
        return False

    # remove any existing container with the same name so redeploys don't
    # collide with a previous run; ignore failure since there may not be one
    run_remote(client, f'bash -c "docker rm -f {project_name} || true"')

    run_cmd = f'bash -c "docker run -d --name {project_name} -p {port}:{port} {project_name}:latest"'
    if not run_remote(client, run_cmd):
        print("An error occurred starting the Docker container")
        return False

    return True

if __name__ == "__main__":
    container = run_container()
    if container:
        print("Docker image built and container started successfully")
