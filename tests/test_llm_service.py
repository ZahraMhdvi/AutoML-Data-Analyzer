
import json
import logging
from types import SimpleNamespace

import httpx
import openai
import pytest

from ml_engine.ai import llm_target_service as llm
from ml_engine.ai.llm_target_service import LLMTargetService, LLMTargetServiceError


PROFILE = {"columns": ["Customer_ID", "spend", "visits", "city"], "columns_info": [], "rows": 100}
NUMERIC = ["spend", "visits"]
REQUEST = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
GOOD = json.dumps({"target_name": "value", "important_features": ["spend", "visits"],
                   "feature_directions": {"spend": 1, "visits": -1}, "reason_en": "ok", "reason_fa": "باشه"})


def _response(text):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text))])


def _status_error(cls, status):
    return cls(message="boom sk-or-v1-SECRETKEY1234567", response=httpx.Response(status, request=REQUEST), body=None)


class ScriptedClient:



    def __init__(self, *outcomes):
        self.outcomes = list(outcomes)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, model, **kwargs):
        self.calls.append(model)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return _response(outcome)


def _service(*outcomes, models=("primary/m", "secondary/m")):
    client = ScriptedClient(*outcomes)
    config = {"api_key": "x" * 30, "models": list(models), "timeout": 5, "base_url": "http://test"}
    return LLMTargetService(config, client=client), client


def test_valid_key_successful_generation():
    service, _ = _service(GOOD)
    suggestion, record = service.suggest(PROFILE, NUMERIC)
    assert suggestion["features"] == ["spend", "visits"]
    assert suggestion["directions"] == {"spend": 1, "visits": -1}
    assert record["status"] == "SUCCESS" and record["successful_model"] == "primary/m"
    assert record["request_id"] and record["latency_ms"] >= 0


def test_invalid_key_is_auth_error_and_stops(caplog):
    service, client = _service(_status_error(openai.AuthenticationError, 401), GOOD)
    with caplog.at_level(logging.WARNING), pytest.raises(LLMTargetServiceError) as info:
        service.suggest(PROFILE, NUMERIC)
    assert info.value.record["error_code"] == "AUTH_ERROR"
    assert client.calls == ["primary/m"]
    assert "SECRETKEY" not in caplog.text and "SECRETKEY" not in json.dumps(info.value.record)


def test_missing_key_is_not_configured(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    assert llm.get_llm_service() is None
    assert "OPENROUTER_API_KEY_MISSING" in llm.config_status()["problems"]
    with pytest.raises(LLMTargetServiceError) as info:
        LLMTargetService({"api_key": "", "models": ["m"], "timeout": 1})
    assert info.value.code == "LLM_NOT_CONFIGURED"


def test_key_update_after_startup_is_picked_up(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    assert llm.get_llm_service() is None
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-" + "a" * 40)
    assert llm.get_llm_service() is not None


def test_timeout_is_categorised():
    service, _ = _service(openai.APITimeoutError(request=REQUEST), openai.APITimeoutError(request=REQUEST))
    with pytest.raises(LLMTargetServiceError) as info:
        service.suggest(PROFILE, NUMERIC)
    assert [a["error_code"] for a in info.value.record["attempts"]] == ["TIMEOUT", "TIMEOUT"]


def test_rate_limit_is_categorised():
    service, _ = _service(_status_error(openai.RateLimitError, 429), GOOD)
    _, record = service.suggest(PROFILE, NUMERIC)
    assert record["attempts"][0]["error_code"] == "RATE_LIMIT"


def test_non_json_response_is_invalid_response():
    service, _ = _service("I think you should use spend.", "```json\n{not json}\n```")
    with pytest.raises(LLMTargetServiceError) as info:
        service.suggest(PROFILE, NUMERIC)
    assert {a["error_code"] for a in info.value.record["attempts"]} == {"INVALID_RESPONSE"}


def test_invalid_column_names_are_rejected():
    bad = json.dumps({"important_features": ["Revenue", "city"], "reason_en": "x"})
    service, _ = _service(bad, bad)
    with pytest.raises(LLMTargetServiceError) as info:
        service.suggest(PROFILE, NUMERIC)
    assert info.value.record["attempts"][0]["error_code"] == "INVALID_COLUMNS"


def test_partially_invalid_columns_are_filtered():
    mixed = json.dumps({"important_features": ["spend", "Revenue"], "reason_en": "x"})
    service, _ = _service(mixed)
    suggestion, _ = service.suggest(PROFILE, NUMERIC)
    assert suggestion["features"] == ["spend"] and suggestion["rejected_features"] == ["Revenue"]


def test_total_failure_across_primary_and_secondary():
    service, client = _service(_status_error(openai.NotFoundError, 404), openai.APITimeoutError(request=REQUEST))
    with pytest.raises(LLMTargetServiceError) as info:
        service.suggest(PROFILE, NUMERIC)
    assert client.calls == ["primary/m", "secondary/m"]
    assert [a["error_code"] for a in info.value.record["attempts"]] == ["MODEL_UNAVAILABLE", "TIMEOUT"]
    assert info.value.code == "LLM_UNAVAILABLE" and info.value.record["status"] == "FAILED"


def test_failover_to_secondary_model():
    service, _ = _service(_status_error(openai.RateLimitError, 429), GOOD)
    _, record = service.suggest(PROFILE, NUMERIC)
    assert record["successful_model"] == "secondary/m"
    assert record["requested_model"] == "primary/m"


def test_statistical_fallback_is_logged_and_tagged(tmp_path, monkeypatch):
    import numpy as np
    import pandas as pd
    import api.core.db as db
    from api.core.db import connect, init_db
    from api.services import project_service

    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "app.db"))
    init_db()
    with connect() as conn:
        conn.execute("INSERT INTO users (name, email, password_hash, created_at) VALUES ('a','a@b.c','x','t')")

    rng = np.random.default_rng(0)
    df = pd.DataFrame({"spend": rng.normal(size=80), "visits": rng.normal(size=80), "tenure": rng.normal(size=80)})
    pid = project_service.create_project(1, "p", "d.csv", df.to_csv(index=False).encode(), df)

    service, _ = _service(openai.APITimeoutError(request=REQUEST), openai.APITimeoutError(request=REQUEST))
    body = project_service.generate_ai_target(1, pid, llm_service=service)

    assert body["source"] == "statistical"
    assert body["llm"]["status"] == "FALLBACK" and body["llm"]["fallback_used"] is True
    assert body["llm"]["fallback_reason"] == "TIMEOUT"
    assert body["llm"]["actual_method"] == "statistical" and body["llm"]["requested_method"] == "llm"
    with connect() as conn:
        row = conn.execute("SELECT status, fallback_reason, actual_method FROM llm_calls").fetchone()
    assert tuple(row) == ("FALLBACK", "TIMEOUT", "statistical")


def test_prompt_profile_contains_no_row_values():
    import pandas as pd
    from ml_engine.column_analyzer import ColumnAnalyzer
    df = pd.DataFrame({"email": [f"user{i}@mail.com" for i in range(30)],
                       "city": ["Tehran", "Isfahan", "Shiraz"] * 10, "spend": range(30)})
    profile = llm.build_prompt_profile(df, ColumnAnalyzer(df).analyze())
    text = json.dumps(profile)
    assert "Tehran" not in text and "user1@mail.com" not in text
    assert profile["privacy"]["row_values_shared"] is False
