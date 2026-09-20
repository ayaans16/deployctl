from unittest.mock import MagicMock

from app import health

GOOD_CONF = """
core {
    port = 3000
}
"""


def test_health_check_passes_when_curl_succeeds(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(GOOD_CONF)

    monkeypatch.setattr(health, "establish_ssh_connection", lambda: MagicMock())

    ran_commands = []

    def fake_run_remote(client, cmd):
        ran_commands.append(cmd)
        return True

    monkeypatch.setattr(health, "run_remote", fake_run_remote)

    assert health.health_check(retries=3, delay_seconds=1) is True
    assert len(ran_commands) == 1
    assert "localhost:3000" in ran_commands[0]
    assert "seq 1 3" in ran_commands[0]


def test_health_check_fails_when_curl_never_succeeds(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(GOOD_CONF)

    monkeypatch.setattr(health, "establish_ssh_connection", lambda: MagicMock())
    monkeypatch.setattr(health, "run_remote", lambda client, cmd: False)

    assert health.health_check(retries=3, delay_seconds=1) is False


def test_health_check_fails_cleanly_without_config(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert health.health_check() is False
