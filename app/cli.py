"""
deployctl command-line interface

ties together lint, build/run, nginx, and ssl into subcommands,
plus a "deploy" command that runs the whole pipeline in order,
stopping at the first step that fails.
"""

import argparse
import os
import sys

from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

from app.paths import resource_path
from app.lint import run_unit_tests
from app.container import run_container
from app.vps import nginx_conf, ssl_certs, establish_ssh_connection, run_remote
from app.screen import create_screen, load_config as load_screen_config

CONFIG_PATH = resource_path("deployctl.conf")

# directories/files that should never get pushed to the VPS
SYNC_EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", ".vscode"}
SYNC_EXCLUDE_FILES = {".env"}


def sync_files():
    loaded = load_screen_config()
    if loaded is None:
        return False
    project_name, _setup_command, _start_command, path_for_project = loaded

    client = establish_ssh_connection()
    if not client:
        return False

    if path_for_project.startswith("~"):
        _stdin, stdout, _stderr = client.exec_command("echo $HOME")
        remote_home = stdout.read().decode().strip()
        path_for_project = remote_home + path_for_project[1:]

    remote_root = f"{path_for_project.rstrip('/')}/{project_name}"

    if not run_remote(client, f'mkdir -p {remote_root}'):
        print("An error occurred creating the remote project directory")
        return False

    local_root = str(resource_path())

    try:
        sftp = client.open_sftp()
        for dirpath, dirnames, filenames in os.walk(local_root):
            dirnames[:] = [d for d in dirnames if d not in SYNC_EXCLUDE_DIRS]

            rel_dir = os.path.relpath(dirpath, local_root)
            remote_dir = remote_root if rel_dir == "." else f"{remote_root}/{rel_dir}"

            if rel_dir != ".":
                if not run_remote(client, f'mkdir -p {remote_dir}'):
                    print(f"An error occurred creating {remote_dir}")
                    sftp.close()
                    return False

            for filename in filenames:
                if filename in SYNC_EXCLUDE_FILES:
                    continue
                local_path = os.path.join(dirpath, filename)
                remote_path = f"{remote_dir}/{filename}"
                sftp.put(local_path, remote_path)
        sftp.close()
    except Exception as e:
        print(f"An error occurred syncing files to the VPS: {e}")
        return False

    return True

def get_how_to_run():
    try:
        config = ConfigFactory.parse_file(str(CONFIG_PATH))
    except FileNotFoundError:
        print(f"Configuration file not found at {CONFIG_PATH}. Please create the configuration file.")
        return None

    try:
        how_to_run = config.get('core.how_to_run')
    except ConfigMissingException:
        print("Configuration file is missing 'core.how_to_run'. Must be 'docker' or 'linux'.")
        return None

    return how_to_run

def run_app():
    how_to_run = get_how_to_run()
    if how_to_run is None:
        return False

    if how_to_run == "docker":
        return run_container()
    elif how_to_run == "linux":
        return create_screen()
    else:
        print(f"Unknown core.how_to_run value: '{how_to_run}'. Must be 'docker' or 'linux'.")
        return False

STEPS = [
    ("lint", run_unit_tests),
    ("sync", sync_files),
    ("run", run_app),
    ("nginx", nginx_conf),
    ("ssl", ssl_certs),
]

def run_deploy():
    for name, step in STEPS:
        print(f"--- running step: {name} ---")
        if not step():
            print(f"Step '{name}' failed. Aborting deployment.")
            return False
    return True

def main():
    parser = argparse.ArgumentParser(prog="deployctl", description="zero-touch deployment CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("lint", help="Run the project's unit tests")
    subparsers.add_parser("sync", help="Push the local project files to the VPS")
    subparsers.add_parser("run", help="Build/start the app (Docker or Linux screen, per config)")
    subparsers.add_parser("nginx", help="Push the nginx config and reload")
    subparsers.add_parser("ssl", help="Install certbot and generate an SSL certificate")
    subparsers.add_parser("deploy", help="Run the full pipeline: lint -> sync -> run -> nginx -> ssl")

    args = parser.parse_args()

    commands = {
        "lint": run_unit_tests,
        "sync": sync_files,
        "run": run_app,
        "nginx": nginx_conf,
        "ssl": ssl_certs,
        "deploy": run_deploy,
    }

    success = commands[args.command]()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
