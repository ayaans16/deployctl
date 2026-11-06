from dotenv import dotenv_values

from app import container, health, init_wizard, lint, rollback, screen, vps


def answers(how="docker", auth="key", **override):
    """Ordered answers for every prompt; a list value feeds several answers to one prompt (re-prompts)."""
    seq = [("name", "myapp"), ("email", "me@example.com"), ("how", how), ("port", "8080"), ("path", "")]
    if how == "linux":
        seq += [("setup", "pip install -r requirements.txt"), ("start", "gunicorn app:app")]
    seq += [
        ("test_folder", ""),
        ("test_cmd", ""),
        ("domain", "example.com"),
        ("nginx", ""),
        ("ip", "1.2.3.4"),
        ("user", "ubuntu"),
        ("auth", auth),
    ]
    seq += [("key", "")] if auth == "key" else [("password", "s3cret!pw")]

    out = []
    for key, value in seq:
        value = override.get(key, value)
        out.extend(value if isinstance(value, list) else [value])
    return out


def feed(monkeypatch, lines):
    remaining = iter(lines)

    def fake(prompt=""):
        try:
            return next(remaining)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", fake)
    monkeypatch.setattr(init_wizard.getpass, "getpass", fake)


def test_generated_config_loads_through_every_module(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    feed(monkeypatch, answers(port=["abc", "99999", "8080"]))  # invalid ports are re-prompted

    assert init_wizard.run_init() is True

    assert vps.load_config() == ("me@example.com", "example.com", "nginx.conf", "myapp")
    assert container.load_config() == ("myapp", "~/apps/", 8080)
    assert screen.load_config() == ("myapp", "true", "true", "~/apps/")
    assert health.load_config() == 8080
    assert rollback.load_config() == ("myapp", "docker", 8080, "~/apps/", "true")
    unit_test_folder, unit_test_command = lint.load_config()
    assert str(unit_test_folder) == "tests"
    assert unit_test_command == "pytest"


def test_key_auth_env_is_owner_only(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    feed(monkeypatch, answers(auth="key"))

    init_wizard.run_init()

    env = tmp_path / ".env"
    assert env.stat().st_mode & 0o777 == 0o600
    values = dotenv_values(env)
    assert values["VPS_SSH_KEY_PATH"] == "~/.ssh/id_ed25519"
    assert "VPS_PASSWORD" not in values


def test_password_is_written_unquoted_and_unsafe_values_are_rejected(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    # " #" would be read as an inline comment by dotenv, so the first attempt must be re-prompted
    feed(monkeypatch, answers(auth="password", password=["abc #def", "s3cret!pw"]))

    init_wizard.run_init()

    assert "can't be stored safely" in capsys.readouterr().out
    text = (tmp_path / ".env").read_text()
    assert "VPS_PASSWORD=s3cret!pw\n" in text  # unquoted: docker --env-file keeps quotes literally
    assert dotenv_values(tmp_path / ".env")["VPS_PASSWORD"] == "s3cret!pw"


def test_linux_mode_asks_for_commands_and_round_trips_quotes(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    setup = 'python -c "print(\'hi\')" && pip install -r requirements.txt'
    feed(monkeypatch, answers(how="linux", setup=setup))

    init_wizard.run_init()

    assert screen.load_config() == ("myapp", setup, "gunicorn app:app", "~/apps/")


def test_existing_files_are_kept_unless_confirmed(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text("KEEP")
    feed(monkeypatch, answers() + ["n"])  # decline the overwrite prompt

    init_wizard.run_init()

    assert (tmp_path / "deployctl.conf").read_text() == "KEEP"
    assert (tmp_path / ".env").exists()  # the file that didn't exist yet is still written

    feed(monkeypatch, answers() + ["y", "y"])  # now overwrite both
    init_wizard.run_init()
    assert "project_name" in (tmp_path / "deployctl.conf").read_text()


def test_gitignore_entries_are_appended_after_confirmation(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".gitignore").write_text("node_modules")  # no trailing newline
    feed(monkeypatch, answers() + [""])  # accept the default (yes)

    init_wizard.run_init()

    assert (tmp_path / ".gitignore").read_text() == "node_modules\n.env\ndeployctl.conf\n"


def test_cancelling_midway_writes_nothing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    feed(monkeypatch, answers()[:4])  # input runs out -> EOFError

    assert init_wizard.run_init() is False
    assert list(tmp_path.iterdir()) == []
