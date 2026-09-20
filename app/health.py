"""
verifies the app is actually responding after a deploy, by curling its port
directly on the VPS (not through nginx/DNS) — this works identically for
both docker and linux modes since both bind core.port locally, and doesn't
depend on nginx or SSL being configured yet.

prerequisite: curl must be installed on the VPS (same category as docker,
nginx, screen, certbot — assumed already present, not auto-installed here).
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
        port = config.get('core.port')
    except ConfigMissingException:
        # missing keys in the config file
        print("Configuration file is missing required keys. Please check the configuration file.")
        return None

    return port


def health_check(retries=10, delay_seconds=2):
    port = load_config()
    if port is None:
        return False

    client = establish_ssh_connection()
    if not client:
        return False

    check_cmd = (
        f'bash -c "for i in $(seq 1 {retries}); do '
        f'curl -sf -o /dev/null http://localhost:{port} && exit 0; '
        f'sleep {delay_seconds}; done; exit 1"'
    )

    if not run_remote(client, check_cmd):
        print(f"Health check failed: app did not respond on port {port} after {retries * delay_seconds}s")
        return False

    print(f"Health check passed: app is responding on port {port}")
    return True


if __name__ == "__main__":
    import sys
    sys.exit(0 if health_check() else 1)
