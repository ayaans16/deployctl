
from app.paths import resource_path


def test_resource_path_resolves_relative_to_cwd(monkeypatch, tmp_path):
    """
    Regression test: resource_path() used to anchor off __file__ (deployctl's
    own install location) instead of the directory the user actually runs
    `deployctl` from. That broke every config lookup once deployctl became
    an installed CLI rather than a script run from inside its own repo.
    """
    monkeypatch.chdir(tmp_path)
    assert resource_path("deployctl.conf") == tmp_path / "deployctl.conf"


def test_resource_path_with_no_parts_returns_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert resource_path() == tmp_path


def test_resource_path_joins_multiple_parts(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert resource_path("a", "b", "c.txt") == tmp_path / "a" / "b" / "c.txt"
