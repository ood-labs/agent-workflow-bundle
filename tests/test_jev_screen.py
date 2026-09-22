import importlib.util
import json
import subprocess
import sys


def load_module(repo_root):
    path = repo_root / "skills/delegate/scripts/jev-screen.py"
    spec = importlib.util.spec_from_file_location("jev_screen", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_finding_triage_policy_matrix(repo_root):
    m = load_module(repo_root)
    assert m.decide_finding("derived_fix", 0.9, 0.95) == "AUTO_APPLY"
    assert m.decide_finding("derived_fix", 0.9, 0.79) == "REVIEW"      # not safe enough
    assert m.decide_finding("derived_fix", 0.5, 0.95) == "REVIEW"      # bucket not confident
    assert m.decide_finding("judgement_call", 0.9, 0.95) == "REVIEW"   # never auto-apply a judgement
    assert m.decide_finding("unresolvable", 0.9, 0.95) == "ASK"
    assert m.decide_finding("unclear", 0.2, 0.1) == "ASK"


def test_finding_triage_questions_cover_every_finding(repo_root):
    m = load_module(repo_root)
    doc = {"doctrine": "small, mechanical", "findings": [{"id": "f1", "claim": "a"}, {"id": "f2", "claim": "b"}]}
    qs = m.build_questions("finding-triage", doc)
    assert set(qs) == {"bucket_f1", "safe_f1", "bucket_f2", "safe_f2"}
    assert qs["bucket_f1"]["type"] == "choice"
    assert "unclear" in qs["bucket_f1"]["criteria"] and "unresolvable" in qs["bucket_f1"]["criteria"]
    assert qs["safe_f1"]["type"] == "noul"
    assert "`findings[0]" in qs["bucket_f1"]["instructions"]


def test_diff_risk_orders_hunks_and_reports_status(repo_root):
    m = load_module(repo_root)
    hunks = [{"id": "h1", "file": "a.py", "summary": "rename"}, {"id": "h2", "file": "b.py", "summary": "new auth path"}]
    answers = {
        "risk_h1": {"type": "noul", "noul": 0.2},
        "risk_h2": {"type": "noul", "noul": 0.9},
        "slice_status": {"type": "choice", "choice": "partial", "confidence": 0.7, "probabilities": {}},
    }
    out = m.decide_diff(answers, hunks)
    assert out["slice_status"] == "partial"
    assert [r["id"] for r in sorted(out["rows"], key=lambda r: r["order"])] == ["h2", "h1"]


def test_cli_skips_without_key(repo_root, tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/jev-screen.py"), "diff-risk"],
                       input=json.dumps({"slice": {}, "hunks": []}), capture_output=True, text=True)
    assert r.returncode == 0
    assert json.loads(r.stdout)["skipped"].startswith("TYPESAFE_API_KEY")


def test_cli_skips_on_bad_input(repo_root, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/jev-screen.py"), "finding-triage"],
                       input="not json", capture_output=True, text=True)
    assert r.returncode == 0
    assert "skipped" in json.loads(r.stdout)


def test_run_skips_on_api_failure(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def boom(key, state, questions):
        raise OSError("no network")
    m.call_api = boom
    out = m.run("finding-triage", {"doctrine": "d", "findings": [{"id": "f1", "claim": "c"}]})
    assert out["skipped"].startswith("API unreachable")


def test_run_finding_triage_with_fake_api(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def fake(key, state, questions):
        return {"usage": {"input_tokens": 10}, "answers": {
            "bucket_f1": {"type": "choice", "choice": "derived_fix", "confidence": 0.9, "probabilities": {}},
            "safe_f1": {"type": "noul", "noul": 0.95}}}
    m.call_api = fake
    out = m.run("finding-triage", {"doctrine": "d", "findings": [{"id": "f1", "claim": "c"}]})
    assert out["rows"][0]["verdict"] == "AUTO_APPLY"
    assert out["usage"]["input_tokens"] == 10


def test_run_skips_when_finding_lacks_id(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    out = m.run("finding-triage", {"doctrine": "d", "findings": [{"claim": "no id"}]})
    assert out["skipped"].startswith("bad input")


def test_run_diff_risk_without_hunks_key_skips_not_crashes(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def fake(key, state, questions):
        return {"usage": {}, "answers": {"slice_status": {"choice": "unclear", "confidence": 0.5}}}
    m.call_api = fake
    out = m.run("diff-risk", {"slice": {}})
    assert isinstance(out, dict)
    assert out["rows"] == [] and out["slice_status"] == "unclear"


def test_malformed_api_numbers_degrade_per_row(repo_root, monkeypatch):
    m = load_module(repo_root)
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")

    def fake(key, state, questions):
        return {"usage": {}, "answers": {
            "bucket_f1": {"type": "choice", "choice": "derived_fix", "confidence": None},
            "safe_f1": {"type": "noul", "noul": "oops"}}}
    m.call_api = fake
    out = m.run("finding-triage", {"doctrine": "d", "findings": [{"id": "f1", "claim": "c"}]})
    assert out["rows"][0]["verdict"] == "REVIEW"
    assert out["rows"][0]["safe_to_auto_apply"] == 0.0


def test_cli_unknown_mode_prints_skipped_json(repo_root):
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/jev-screen.py"), "nope"],
                       input="", capture_output=True, text=True)
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "unknown mode" in out["skipped"]


def test_cli_reads_utf8_stdin(repo_root, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "x")
    payload = json.dumps({"slice": {"pass_criterion": "café — ünïcode"}, "hunks": []}, ensure_ascii=False)
    r = subprocess.run([sys.executable, str(repo_root / "skills/delegate/scripts/jev-screen.py"), "finding-triage"],
                       input=payload, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "skipped" in out
