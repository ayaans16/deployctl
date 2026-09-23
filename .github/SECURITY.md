# Security Policy

## Reporting a Vulnerability

If you find a security issue in `deployctl`, please report it privately rather than opening a public GitHub issue — this gives us time to fix it before it's disclosed.

- Email: [your-email@example.com] *(replace with a real contact you check)*
- Please include: a description of the issue, steps to reproduce, and the potential impact
- We'll acknowledge reports within a few days and aim to have a fix or mitigation before any public disclosure

## Supported Versions

`deployctl` is a single-branch project (`main`) — only the latest commit is supported. There are no maintained release branches to backport fixes to.

## Security Considerations Specific to This Project

`deployctl` holds real credentials and executes commands on a real remote server, so a few things are worth understanding if you're auditing it or contributing to it:

### Credentials

- `.env` holds `VPS_PASSWORD` or `VPS_SSH_KEY_PATH` in plaintext. It's gitignored by default — **never commit it**, and never log its contents. Prefer `VPS_SSH_KEY_PATH` (SSH key auth) over `VPS_PASSWORD` where possible; it's required anyway for any VPS that doesn't support password auth (e.g. AWS EC2's default Ubuntu AMI).
- `deployctl.conf` is also gitignored, since it can contain domain names and other environment-specific details users may not want public.

### SSH Connections (`app/vps.py`)

- `establish_ssh_connection()` uses `paramiko.RejectPolicy()` with `load_system_host_keys()` — it will **refuse** to connect to a host whose key isn't already in `~/.ssh/known_hosts`, rather than silently trusting whatever key is presented. Do not change this to `AutoAddPolicy()` — that would make every connection vulnerable to a MITM attack with no warning.
- All remote commands go through `run_remote()`, which checks the actual exit status of the command rather than assuming success — this matters because a silently-failed remote command (e.g. a permission error) could otherwise leave the VPS in an inconsistent state without anyone noticing.

### Privilege Escalation on the VPS

- Commands that need root (writing to `/etc/nginx/`, installing packages, reloading services) run via `sudo` over SSH, which requires the deploy user to have **passwordless sudo scoped to specific commands** configured in `/etc/sudoers.d/` on the VPS — not blanket `NOPASSWD: ALL`. See the README for the exact sudoers entries this project expects.
- SFTP (`sftp.put()`) has **no privilege escalation mechanism** — files can only be written to paths the SSH user already owns. Anything destined for a root-owned path (like `/etc/nginx/sites-available/`) is uploaded to a user-writable location first (`/tmp`), then moved into place with an explicit `sudo mv`.

### Dependencies

- Runtime dependencies are intentionally minimal (`pyhocon`, `paramiko`, `python-dotenv`) and each one is load-bearing — resist adding a new dependency for something that can be done in a few lines of stdlib.
- If you're proposing a new dependency, check its publisher/maintainer reputation and recent commit history before adding it. This project previously had a supply-chain scare from a since-removed dependency that turned out to have hallmarks of a typosquatting package (multiple duplicate package names shipped under one install, no verifiable author, an unused networking dependency) — dependencies get real scrutiny here, not just "does it work."

### Command Construction

- Several modules build shell command strings via f-strings (e.g. `docker build -t {project_name}:latest`) rather than fully parameterized subprocess calls, because they're executed remotely via SSH `exec_command`, not locally. Values that end up in these strings come from `deployctl.conf`, which is assumed to be trusted (the person running `deployctl` controls their own config) — this is **not** safe against untrusted input, and any feature that accepts external/user-supplied input (e.g. a web-facing trigger for deploys) would need proper shell-escaping added first.

## Scope

This policy covers the `deployctl` codebase itself. It does not cover the security configuration of the VPS you deploy to (firewall rules, OS patching, sudoers setup) — that remains the operator's responsibility, though the README documents the minimum secure setup this tool expects.
