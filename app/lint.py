"""
this will be where we run the linting for the project by running the unit tests
if all unit tests pass, it will move towards the docker portion
if one unit test fails, it will stop the process and see what went wrong, and return the error
"""

from app.paths import resource_path
from pathlib import Path

from pyhocon import ConfigFactory
from pyhocon.exceptions import ConfigMissingException

import subprocess
import shlex

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
        unit_test_folder = Path(config.get('lint.unit_test_folder'))
        unit_test_command = config.get('lint.unit_test_command')
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return unit_test_folder, unit_test_command

def run_unit_tests():
    # call load config
    loaded = load_config()

    if loaded is None:
        return None

    unit_test_folder, unit_test_command = loaded

    # try-catch block to make sure the unit test folder exists and is a directory
    try:
        unit_test_folder.resolve(strict=True)
    except FileNotFoundError:
        print("Unit test folder does not exist. Modify the configuration file")
        return False
    else:
        if unit_test_folder.is_dir():
            print(f"Running unit tests in {unit_test_folder}")
        else:
            print("This is not a directory. Modify the configuration file")
            return False

    # validate that the unit test command is not empty
    if unit_test_command:
        print("Running the unit test command")
    else:
        print("The unit test command is empty. Modify the configuration file")
        return False

    # cut the unit test command into a list of arguments
    unit_test_command_list = shlex.split(unit_test_command)
    res = subprocess.run(unit_test_command_list, 
                        cwd=unit_test_folder, # current working directory
                        capture_output=True,  # must capture the result
                        text=True)

    # something failed
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)

        print(f"A unit test failed with return code {res.returncode}. View above for more information")
        return False

    # all unit tests passed
    print("All unit tests passed!")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if run_unit_tests() else 1)