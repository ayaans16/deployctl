"""
all docker logic lives here
prerequisite: must have a dockerfile !!!!
"""

import docker

from paths import resource_path
from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

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
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return project_name

def docker_daemon():
    try:
        client = docker.from_env()
    except Exception as e:
        print(f"Docker client could not be initialized. {e}")
        return False
    return client

def build_image():
    client = docker_daemon()

    if not client:
        return False
    project_name = load_config()
    if not project_name:
        return False

    # assumption is Dockerfile is in root
    dockerfile_path = resource_path("Dockerfile")

    # dockerfile dne
    if not dockerfile_path.exists():
        print("Dockerfile cannot be found. Please create one")
        return False

    # empty Dockerfile
    if dockerfile_path.stat().st_size == 0:
        print("Dockerfile is empty, you must write content in it")
        return False
    
    try:
        image = client.images.build(path=str(resource_path()), tag=f"{project_name}:1.0", rm=True)
    except (docker.errors.BuildError, docker.errors.APIError) as e:
        print(f"An error occurred while trying to build the image: {e}")
        return False

    return True

if __name__ == "__main__":
    client = docker_daemon()
    if client:
        print("Docker client initialized successfully")
    image = build_image()
    if image:
        print("Image built successfully")