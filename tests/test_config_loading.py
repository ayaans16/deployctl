from app.lint import load_config as load_lint_config
from app.vps import load_config as load_vps_config

GOOD_CONF = """
core {
    project_name = "myapp"
    email_address = "me@example.com"
}
lint {
    unit_test_folder = "/tmp"
    unit_test_command = "pytest"
}
web {
    nginx_config_filename = "nginx.conf"
    domain = "example.com"
}
"""


def test_load_config_returns_none_when_file_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert load_lint_config() is None


def test_load_config_returns_none_when_keys_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text("core { project_name = \"x\" }")
    assert load_lint_config() is None


def test_lint_load_config_returns_expected_values(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(GOOD_CONF)

    unit_test_folder, unit_test_command = load_lint_config()
    assert str(unit_test_folder) == "/tmp"
    assert unit_test_command == "pytest"


def test_vps_load_config_returns_expected_values(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "deployctl.conf").write_text(GOOD_CONF)

    email, domain, nginx_config_filename, project_name = load_vps_config()
    assert email == "me@example.com"
    assert domain == "example.com"
    assert nginx_config_filename == "nginx.conf"
    assert project_name == "myapp"
