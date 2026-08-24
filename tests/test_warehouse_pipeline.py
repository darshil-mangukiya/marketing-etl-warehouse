from scripts.run_warehouse_pipeline import _run_dbt_build


def test_dbt_build_command_uses_temp_target_and_logs(monkeypatch):
    captured = {}

    class Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(command, cwd, text, capture_output):
        captured["command"] = command
        captured["cwd"] = cwd
        captured["text"] = text
        captured["capture_output"] = capture_output
        return Result()

    monkeypatch.setattr("scripts.run_warehouse_pipeline.subprocess.run", fake_run)
    result = _run_dbt_build("mart")

    assert result["return_code"] == 0
    assert "--log-path" in captured["command"]
    target_path = captured["command"][captured["command"].index("--target-path") + 1]
    assert target_path.endswith("marketing-etl-platform-dbt/target")
    assert "--full-refresh" in captured["command"]
    assert captured["command"][-2:] == ["--select", "mart"]
