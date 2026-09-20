from unittest.mock import MagicMock

from app import rollback

DOCKER_CONF = """
core {
    project_name = "myapp"
    how_to_run = "docker"
    port = 3000
    path_for_project = "/home/user/apps/"
    start_command = "gunicorn app:app"
}
"""

LINUX_CONF = """
core {
    project_name = "myapp"
    how_to_run = "linux"
    port = 3000
    path_for_project = "/home/user/apps/"
    start_command = "gunicorn app:app"
}
"""


def test_docker_rollback_runs_previous_tag(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(DOCKER_CONF)
    monkeypatch.setattr(rollback, "establish_ssh_connection", lambda: MagicMock())

    ran_commands = []

    def fake_run_remote(client, cmd):
        ran_commands.append(cmd)
        return True  # previous image exists, rm succeeds, run succeeds

    monkeypatch.setattr(rollback, "run_remote", fake_run_remote)

    assert rollback.rollback() is True
    assert "docker image inspect myapp:previous" in ran_commands[0]
    assert any("docker run -d --name myapp" in c and "myapp:previous" in c for c in ran_commands)


def test_docker_rollback_fails_when_no_previous_image(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(DOCKER_CONF)
    monkeypatch.setattr(rollback, "establish_ssh_connection", lambda: MagicMock())
    # the very first run_remote call (the existence check) fails
    monkeypatch.setattr(rollback, "run_remote", lambda client, cmd: False)

    assert rollback.rollback() is False


def test_linux_rollback_restores_previous_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(LINUX_CONF)
    monkeypatch.setattr(rollback, "establish_ssh_connection", lambda: MagicMock())

    ran_commands = []

    def fake_run_remote(client, cmd):
        ran_commands.append(cmd)
        return True

    monkeypatch.setattr(rollback, "run_remote", fake_run_remote)

    assert rollback.rollback() is True
    assert "test -d /home/user/apps/myapp.previous" in ran_commands[0]
    assert any("mv /home/user/apps/myapp.previous /home/user/apps/myapp" in c for c in ran_commands)
    assert any(c.startswith("screen -dmS myapp") for c in ran_commands)


def test_linux_rollback_fails_when_no_previous_directory(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(LINUX_CONF)
    monkeypatch.setattr(rollback, "establish_ssh_connection", lambda: MagicMock())
    monkeypatch.setattr(rollback, "run_remote", lambda client, cmd: False)

    assert rollback.rollback() is False
