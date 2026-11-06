from app import cli, ui


def _steps(*specs):
    calls = []

    def make(name, result):
        def step():
            calls.append(name)
            return result

        return name, step

    return [make(name, result) for name, result in specs], calls


def test_all_stages_pass(monkeypatch, capsys):
    steps, calls = _steps(("lint", True), ("sync", True))
    monkeypatch.setattr(cli, "STEPS", steps)

    assert cli.run_deploy() is True

    out = capsys.readouterr().out
    assert calls == ["lint", "sync"]
    assert "[1/2] lint" in out and "[2/2] sync" in out
    assert "Summary" in out
    assert "\033" not in out  # captured output isn't a terminal: no color codes


def test_failure_stops_the_pipeline_and_marks_the_rest_skipped(monkeypatch, capsys):
    steps, calls = _steps(("lint", True), ("sync", False), ("nginx", True))
    monkeypatch.setattr(cli, "STEPS", steps)

    assert cli.run_deploy() is False

    out = capsys.readouterr().out
    assert calls == ["lint", "sync"]  # nginx never ran
    assert "Aborting deployment." in out
    assert "nginx" in out and "not run" in out


def test_failed_health_check_triggers_rollback(monkeypatch, capsys):
    steps, calls = _steps(("lint", True), ("health_check", False), ("nginx", True))
    monkeypatch.setattr(cli, "STEPS", steps)
    rolled_back = []
    monkeypatch.setattr(cli, "rollback", lambda: rolled_back.append(True) or True)

    assert cli.run_deploy() is False

    assert rolled_back == [True]
    assert calls == ["lint", "health_check"]
    assert "rollback" in capsys.readouterr().out


def test_other_failures_do_not_trigger_rollback(monkeypatch):
    steps, _ = _steps(("lint", False))
    monkeypatch.setattr(cli, "STEPS", steps)
    monkeypatch.setattr(cli, "rollback", lambda: (_ for _ in ()).throw(AssertionError("should not roll back")))

    assert cli.run_deploy() is False


def test_failed_rollback_asks_for_manual_intervention(monkeypatch, capsys):
    steps, _ = _steps(("health_check", False))
    monkeypatch.setattr(cli, "STEPS", steps)
    monkeypatch.setattr(cli, "rollback", lambda: False)

    cli.run_deploy()

    assert "manual intervention required" in capsys.readouterr().out


def test_steps_that_return_none_count_as_failures(monkeypatch):
    # run_unit_tests() returns None (not False) when the config can't be loaded
    monkeypatch.setattr(cli, "STEPS", [("lint", lambda: None)])

    assert cli.run_deploy() is False


def test_color_only_on_a_terminal_and_respects_no_color(monkeypatch):
    monkeypatch.setattr(ui.sys.stdout, "isatty", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    assert ui.paint("x", "green") == "\033[32mx\033[0m"

    monkeypatch.setenv("NO_COLOR", "1")
    assert ui.paint("x", "green") == "x"
