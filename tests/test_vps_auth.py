from unittest.mock import MagicMock

from app import vps


def _patch_client(monkeypatch):
    fake_client = MagicMock()
    monkeypatch.setattr(vps.paramiko, "SSHClient", lambda: fake_client)
    return fake_client


def test_prefers_key_auth_when_key_path_is_set(monkeypatch):
    fake_client = _patch_client(monkeypatch)
    monkeypatch.setenv("VPS_IP", "1.2.3.4")
    monkeypatch.setenv("VPS_USER", "ubuntu")
    monkeypatch.setenv("VPS_SSH_KEY_PATH", "~/.ssh/deployctl_aws")
    monkeypatch.delenv("VPS_PASSWORD", raising=False)
    monkeypatch.setattr(vps, "load_dotenv", lambda: None)

    result = vps.establish_ssh_connection()

    assert result is fake_client
    _args, kwargs = fake_client.connect.call_args
    assert "key_filename" in kwargs
    assert kwargs["key_filename"].endswith("/.ssh/deployctl_aws")
    assert "password" not in kwargs


def test_falls_back_to_password_auth_when_no_key_path(monkeypatch):
    fake_client = _patch_client(monkeypatch)
    monkeypatch.setenv("VPS_IP", "1.2.3.4")
    monkeypatch.setenv("VPS_USER", "ubuntu")
    monkeypatch.setenv("VPS_PASSWORD", "hunter2")
    monkeypatch.delenv("VPS_SSH_KEY_PATH", raising=False)
    monkeypatch.setattr(vps, "load_dotenv", lambda: None)

    result = vps.establish_ssh_connection()

    assert result is fake_client
    _args, kwargs = fake_client.connect.call_args
    assert kwargs["password"] == "hunter2"
    assert "key_filename" not in kwargs


def test_fails_cleanly_with_neither_password_nor_key(monkeypatch):
    _patch_client(monkeypatch)
    monkeypatch.setenv("VPS_IP", "1.2.3.4")
    monkeypatch.setenv("VPS_USER", "ubuntu")
    monkeypatch.delenv("VPS_PASSWORD", raising=False)
    monkeypatch.delenv("VPS_SSH_KEY_PATH", raising=False)
    monkeypatch.setattr(vps, "load_dotenv", lambda: None)

    assert vps.establish_ssh_connection() is False
