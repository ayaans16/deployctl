"""
interactive setup: asks a handful of questions and writes deployctl.conf and
.env into the current directory, so nobody has to hand-edit the example files.

stdlib only. the VPS password is read with getpass so it isn't echoed, and
.env is written with owner-only permissions.
"""

import getpass
import json
import os
import re
from pathlib import Path

from app.paths import resource_path

GITIGNORE_ENTRIES = (".env", "deployctl.conf")


def ask(prompt, default=None, validate=None, secret=False):
    reader = getpass.getpass if secret else input
    suffix = f" [{default}]" if default else ""
    while True:
        value = reader(f"{prompt}{suffix}: ").strip() or (default or "")
        if not value:
            print("  a value is required")
            continue
        error = validate(value) if validate else None
        if error:
            print(f"  {error}")
            continue
        return value


def ask_yes_no(prompt, default=False):
    hint = "Y/n" if default else "y/N"
    answer = input(f"{prompt} [{hint}]: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def _choice(*options):
    def check(value):
        return None if value in options else f"choose one of: {', '.join(options)}"

    return check


def _valid_name(value):
    # used for the docker image tag, screen session name, remote directory and nginx site file
    if re.fullmatch(r"[a-z0-9][a-z0-9_-]*", value):
        return None
    return "use lowercase letters, digits, '-' and '_' (it becomes a docker image name and directory)"


def _valid_port(value):
    return None if value.isdigit() and 1 <= int(value) <= 65535 else "enter a port between 1 and 65535"


def _valid_email(value):
    return None if "@" in value and " " not in value else "enter a valid email address"


def _valid_domain(value):
    ok = "." in value and not re.search(r"[\s/]", value)
    return None if ok else "enter a bare domain like example.com (no spaces or slashes)"


def _no_spaces(value):
    return None if not re.search(r"\s", value) else "spaces aren't supported here"


def _env_safe(value):
    # .env is read by python-dotenv and, via the docker wrapper, by `docker --env-file`,
    # which doesn't strip quotes — so values must be safe to store completely unquoted
    if value != value.strip() or " #" in value or value[0] in "'\"":
        return "can't be stored safely in .env (leading/trailing space, ' #' or a leading quote)"
    return None


def _slug(name):
    return re.sub(r"[^a-z0-9_-]+", "-", name.lower()).strip("-_")


def gather():
    default_name = _slug(Path.cwd().name) or None
    values = {}

    print("Project")
    values["project_name"] = ask("  Project name", default_name, _valid_name)
    values["email_address"] = ask("  Email (for Let's Encrypt notices)", validate=_valid_email)
    values["how_to_run"] = ask("  Run the app with docker or linux (GNU screen)?", "docker", _choice("docker", "linux"))
    values["port"] = ask("  Port your app listens on", "3000", _valid_port)
    values["path_for_project"] = ask("  Parent directory on the VPS", "~/apps/", _no_spaces)

    if values["how_to_run"] == "linux":
        values["setup_command"] = ask("  Setup command (installs dependencies)")
        values["start_command"] = ask("  Start command")
    else:
        values["setup_command"] = values["start_command"] = "true"

    print("\nTests")
    values["unit_test_folder"] = ask("  Unit test folder", "tests", _no_spaces)
    values["unit_test_command"] = ask("  Unit test command", "pytest")

    print("\nWeb")
    values["domain"] = ask("  Domain (its DNS must point at the VPS)", validate=_valid_domain)
    values["nginx_config_filename"] = ask("  Nginx config filename", "nginx.conf", _no_spaces)

    print("\nVPS")
    values["vps_ip"] = ask("  VPS IP or hostname", validate=lambda v: _no_spaces(v) or _env_safe(v))
    values["vps_user"] = ask("  SSH user", validate=lambda v: _no_spaces(v) or _env_safe(v))
    values["auth"] = ask("  Authenticate with an SSH key or a password?", "key", _choice("key", "password"))
    if values["auth"] == "key":
        values["ssh_key_path"] = ask("  Path to your private key", "~/.ssh/id_ed25519", _env_safe)
    else:
        values["vps_password"] = ask("  Password (hidden)", validate=_env_safe, secret=True)

    return values


def _q(value):
    # json string escaping is valid HOCON quoting too
    return json.dumps(value, ensure_ascii=False)


def render_conf(v):
    return f"""core {{
    project_name = {_q(v["project_name"])}
    email_address = {_q(v["email_address"])}

    # how the app runs on the VPS: "docker" or "linux" (a GNU screen session)
    how_to_run = {_q(v["how_to_run"])}

    # setup_command and start_command are only used when how_to_run = "linux"
    setup_command = {_q(v["setup_command"])}
    start_command = {_q(v["start_command"])}

    # parent directory on the VPS; the project is deployed to <path>/<project_name>
    path_for_project = {_q(v["path_for_project"])}

    # port the app listens on (docker run -p PORT:PORT, health check, nginx proxy_pass)
    port = {int(v["port"])}
}}

lint {{
    unit_test_folder = {_q(v["unit_test_folder"])}
    unit_test_command = {_q(v["unit_test_command"])}
}}

web {{
    nginx_config_filename = {_q(v["nginx_config_filename"])}
    domain = {_q(v["domain"])}
}}
"""


def render_env(v):
    lines = ["# vps information", f"VPS_IP={v['vps_ip']}", f"VPS_USER={v['vps_user']}", ""]
    if v["auth"] == "key":
        lines.append(f"VPS_SSH_KEY_PATH={v['ssh_key_path']}")
    else:
        lines.append(f"VPS_PASSWORD={v['vps_password']}")
    return "\n".join(lines) + "\n"


def _write(path, content, mode):
    if path.exists() and not ask_yes_no(f"{path.name} already exists. Overwrite?"):
        print(f"  kept existing {path.name}")
        return False
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
    with os.fdopen(fd, "w") as handle:
        handle.write(content)
    os.chmod(path, mode)  # os.open only applies the mode when it creates the file
    print(f"  wrote {path.name}")
    return True


def _offer_gitignore(directory):
    gitignore = directory / ".gitignore"
    if not gitignore.exists() and not (directory / ".git").exists():
        return

    text = gitignore.read_text() if gitignore.exists() else ""
    present = {line.strip() for line in text.splitlines()}
    missing = [entry for entry in GITIGNORE_ENTRIES if entry not in present]
    if not missing:
        return

    print(f"\n{' and '.join(missing)} hold credentials or environment-specific details and shouldn't be committed.")
    if ask_yes_no("Add them to .gitignore?", default=True):
        prefix = "" if not text or text.endswith("\n") else "\n"
        with open(gitignore, "a") as handle:
            handle.write(prefix + "\n".join(missing) + "\n")
        print("  updated .gitignore")


def run_init():
    print("deployctl setup — press Enter to accept the [default].\n")
    directory = resource_path()
    try:
        values = gather()
        print()
        _write(directory / "deployctl.conf", render_conf(values), 0o644)
        _write(directory / ".env", render_env(values), 0o600)
        _offer_gitignore(directory)
    except (EOFError, KeyboardInterrupt):
        print("\nSetup cancelled.")
        return False

    print("\nNext steps:")
    print(f"  - make sure {values['nginx_config_filename']} exists in this directory (your nginx server block)")
    if values["how_to_run"] == "docker":
        print("  - docker mode needs a Dockerfile in this directory")
    print("  - run `deployctl deploy`, or try one stage at a time (`deployctl lint`, `deployctl sync`, ...)")
    return True
