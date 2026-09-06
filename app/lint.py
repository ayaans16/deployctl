"""
this will be where we run the linting for the project by running the unit tests
if all unit tests pass, it will move towards the docker portion
if one unit test fails, it will stop the process and see what went wrong, and return the error
"""

from paths import resource_path
from pyhocon import ConfigFactory

CONFIG_PATH = resource_path("deployctl.conf")
config = ConfigFactory.parse_file(str(CONFIG_PATH))

unit_test_folder = config.get('lint.unit_test_folder')
unit_test_command = config.get('lint.unit_test_command')

