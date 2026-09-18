from unittest.mock import MagicMock

from app import screen

GOOD_CONF = """
core {
    project_name = "myapp"
    setup_command = "pip install -r requirements.txt"
    start_command = "gunicorn app:app"
    path_for_project = "/home/user/apps/"
}
"""


def test_create_screen_builds_expected_commands(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(GOOD_CONF)

    fake_client = MagicMock()
    monkeypatch.setattr(screen, "establish_ssh_connection", lambda: fake_client)

    ran_commands = []

    def fake_run_remote(client, cmd):
        ran_commands.append(cmd)
        return True

    monkeypatch.setattr(screen, "run_remote", fake_run_remote)

    assert screen.create_screen() is True
    assert ran_commands == [
        'bash -c "mkdir -p /home/user/apps/myapp"',
        'bash -c "cd /home/user/apps/myapp && pip install -r requirements.txt"',
        'screen -dmS myapp bash -c "cd /home/user/apps/myapp && gunicorn app:app"',
    ]


def test_create_screen_stops_early_when_setup_fails(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(GOOD_CONF)

    monkeypatch.setattr(screen, "establish_ssh_connection", lambda: MagicMock())

    calls = {"count": 0}

    def fake_run_remote(client, cmd):
        calls["count"] += 1
        # mkdir succeeds, setup_command fails
        return calls["count"] != 2

    monkeypatch.setattr(screen, "run_remote", fake_run_remote)

    assert screen.create_screen() is False
    # should never have reached the screen -dmS call
    assert calls["count"] == 2
