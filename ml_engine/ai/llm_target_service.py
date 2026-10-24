

import json
import logging
import os
import re
import threading
import time
import uuid

from dotenv import load_dotenv

from ml_engine.errors import AppError

try:
    import openai
    from openai import OpenAI
except Exception:
    openai = None
    OpenAI = None


load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_PRIMARY_MODEL = "google/gemma-4-31b-it:free"
DEFAULT_FALLBACK_MODELS = [
    "qwen/qwen3.8-27b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/free",
]

SYSTEM_PROMPT = (
    "You are a careful data scientist. Reply with exactly one valid JSON object and nothing else."
)

ERROR_CODES = (
    "AUTH_ERROR", "RATE_LIMIT", "TIMEOUT", "CONNECTION_ERROR", "MODEL_UNAVAILABLE",
    "INVALID_RESPONSE", "INVALID_COLUMNS",
)

_KEY_PATTERN = re.compile(r"(sk-[A-Za-z0-9_\-]{6,}|Bearer\s+[A-Za-z0-9_\-\.]{6,})")


def scrub(text):

    return _KEY_PATTERN.sub("[REDACTED]", str(text))


class LLMTargetServiceError(AppError):


    def __init__(self, code, record=None, params=None):
        self.record = record or {}
        super().__init__(code, params or {})

    @property
    def details(self):
        return [f"{a['model']}: {a.get('error_code')}" for a in self.record.get("attempts", [])]


class InvalidLLMOutput(Exception):
    def __init__(self, code, detail=""):
        self.code = code
        super().__init__(detail)


def categorize(exc):


    if isinstance(exc, InvalidLLMOutput):
        return exc.code
    if openai is not None:
        if isinstance(exc, (openai.AuthenticationError, openai.PermissionDeniedError)):
            return "AUTH_ERROR"
        if isinstance(exc, openai.RateLimitError):
            return "RATE_LIMIT"
        if isinstance(exc, openai.APITimeoutError):
            return "TIMEOUT"
        if isinstance(exc, openai.NotFoundError):
            return "MODEL_UNAVAILABLE"
        if isinstance(exc, openai.APIConnectionError):
            return "CONNECTION_ERROR"
        if isinstance(exc, openai.APIStatusError):
            status = getattr(exc, "status_code", None)
            if status in (401, 403):
                return "AUTH_ERROR"
            if status == 429:
                return "RATE_LIMIT"
            if status in (404, 410):
                return "MODEL_UNAVAILABLE"
            if status == 408:
                return "TIMEOUT"
            return "CONNECTION_ERROR"
    if isinstance(exc, TimeoutError):
        return "TIMEOUT"
    if isinstance(exc, (ValueError, json.JSONDecodeError, KeyError, TypeError)):
        return "INVALID_RESPONSE"
    return "CONNECTION_ERROR"



def read_config():
    load_dotenv(override=False)
    primary = os.getenv("OPENROUTER_MODEL", "").strip() or DEFAULT_PRIMARY_MODEL
    fallbacks = [m.strip() for m in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",") if m.strip()]
    models = []
    for model in [primary] + (fallbacks or DEFAULT_FALLBACK_MODELS):
        if model not in models:
            models.append(model)
    return {
        "api_key": os.getenv("OPENROUTER_API_KEY", "").strip(),
        "models": models,
        "timeout": float(os.getenv("OPENROUTER_TIMEOUT", "45")),
        "base_url": os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
    }


def config_status():


    config = read_config()
    problems = []
    if not config["api_key"]:
        problems.append("OPENROUTER_API_KEY_MISSING")
    elif len(config["api_key"]) < 20:
        problems.append("OPENROUTER_API_KEY_MALFORMED")
    if config["timeout"] <= 0:
        problems.append("OPENROUTER_TIMEOUT_INVALID")
    if OpenAI is None:
        problems.append("OPENAI_SDK_MISSING")
    return {
        "configured": not problems,
        "problems": problems,
        "models": config["models"],
        "timeout_s": config["timeout"],
        "key_fingerprint": ("…" + config["api_key"][-4:]) if config["api_key"] else None,
    }


_lock = threading.Lock()
_cache = {"fingerprint": None, "service": None}


def get_llm_service():

    config = read_config()
    fingerprint = (config["api_key"], tuple(config["models"]), config["timeout"], config["base_url"])
    with _lock:
        if _cache["fingerprint"] != fingerprint:
            _cache["fingerprint"] = fingerprint
            _cache["service"] = LLMTargetService(config) if config["api_key"] and OpenAI else None
        return _cache["service"]



def build_prompt_profile(df, column_analysis):


    columns = []
    for column, info in column_analysis.items():
        series = df[column]
        entry = {"name": str(column), "type": info["semantic_type"],
                 "missing_ratio": round(float(series.isna().mean()), 3)}
        if info["semantic_type"] == "numerical":
            q = series.quantile([0.25, 0.5, 0.75])
            entry.update({"p25": _r(q.iloc[0]), "median": _r(q.iloc[1]), "p75": _r(q.iloc[2])})
        elif info["semantic_type"] != "identifier":
            entry["distinct_values"] = int(series.nunique(dropna=True))
        columns.append(entry)

    return {
        "columns": [str(c) for c in df.columns],
        "columns_info": columns,
        "rows": int(len(df)),
        "privacy": {"row_values_shared": False, "category_labels_shared": False,
                    "shared_fields": ["column names", "semantic types", "missing ratios",
                                      "numeric quartiles", "distinct-value counts"]},
    }


def _r(value):
    try:
        return round(float(value), 3)
    except (TypeError, ValueError):
        return None


class LLMTargetService:

    def __init__(self, config=None, client=None):
        config = config or read_config()
        if not config.get("api_key") and client is None:
            raise LLMTargetServiceError("LLM_NOT_CONFIGURED")
        self.models = list(config["models"])
        self.timeout = config["timeout"]
        self.client = client or OpenAI(
            api_key=config["api_key"], base_url=config.get("base_url", OPENROUTER_BASE_URL),
            timeout=self.timeout, max_retries=0,
        )

    @staticmethod
    def build_prompt(profile):
        return (
            "Design a classification pseudo-target for a tabular dataset that has no obvious label.\n"
            "Choose 2 to 4 existing NUMERIC columns whose combination defines a meaningful ordinal "
            "level (Low / Medium / High). Ignore identifier columns. Use only names from \"columns\".\n"
            "For each chosen column give its direction: 1 if larger values mean a higher level, -1 otherwise.\n"
            "Explain the target briefly in English (reason_en) and in Persian (reason_fa).\n"
            "Return only this JSON object:\n"
            '{"target_name": "...", "important_features": ["col"], "feature_directions": {"col": 1}, '
            '"reason_en": "...", "reason_fa": "..."}\n\n'
            "Dataset summary (aggregated, no row values):\n"
            + json.dumps({k: v for k, v in profile.items() if k != "privacy"}, ensure_ascii=False)
        )

    @staticmethod
    def extract_json(text):
        if not text or not str(text).strip():
            raise InvalidLLMOutput("INVALID_RESPONSE", "empty response")
        cleaned = str(text).strip()
        fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
        if fence:
            cleaned = fence.group(1)
        else:
            start, end = cleaned.find("{"), cleaned.rfind("}")
            if start != -1 and end > start:
                cleaned = cleaned[start:end + 1]
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise InvalidLLMOutput("INVALID_RESPONSE", f"non-JSON response: {exc}")

    @staticmethod
    def response_text(response):
        choices = getattr(response, "choices", None)
        if not choices:
            raise InvalidLLMOutput("INVALID_RESPONSE", "no choices")
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None) or getattr(message, "reasoning", None)
        if not content:
            raise InvalidLLMOutput("INVALID_RESPONSE", "empty content")
        return content

    @staticmethod
    def validate(result, profile, numeric_columns):
        if not isinstance(result, dict):
            raise InvalidLLMOutput("INVALID_RESPONSE", "not an object")
        features = result.get("important_features")
        if not isinstance(features, list) or not features:
            raise InvalidLLMOutput("INVALID_RESPONSE", "important_features missing")
        if not (result.get("reason_en") or result.get("reason") or result.get("reason_fa")):
            raise InvalidLLMOutput("INVALID_RESPONSE", "reason missing")

        available = set(profile.get("columns", []))
        valid = [f for f in features if isinstance(f, str) and f in available and f in numeric_columns]
        invalid = [f for f in features if f not in valid]
        if not valid:
            raise InvalidLLMOutput("INVALID_COLUMNS", f"no valid numeric columns among {invalid}")

        directions = result.get("feature_directions") or {}
        if not isinstance(directions, dict):
            directions = {}
        clean_directions = {}
        for feature in valid:
            try:
                clean_directions[feature] = -1 if float(directions.get(feature, 1)) < 0 else 1
            except (TypeError, ValueError):
                clean_directions[feature] = 1

        return {
            "features": valid,
            "rejected_features": invalid,
            "directions": clean_directions,
            "target_name": str(result.get("target_name") or "generated_target")[:80],
            "reason_en": str(result.get("reason_en") or result.get("reason") or "")[:1200],
            "reason_fa": str(result.get("reason_fa") or "")[:1200],
        }

    def suggest(self, profile, numeric_columns, request_id=None):


        prompt = self.build_prompt(profile)
        record = {
            "request_id": request_id or uuid.uuid4().hex,
            "requested_method": "llm",
            "requested_model": self.models[0],
            "successful_model": None,
            "attempts": [],
            "status": "FAILED",
        }
        started = time.perf_counter()

        for model in self.models:
            attempt_start = time.perf_counter()
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT},
                              {"role": "user", "content": prompt}],
                    temperature=0.2,
                    extra_headers={"HTTP-Referer": "http://localhost", "X-Title": "GuidML"},
                )
                suggestion = self.validate(self.extract_json(self.response_text(response)), profile, numeric_columns)
                record["attempts"].append({"model": model, "error_code": None,
                                           "latency_ms": round((time.perf_counter() - attempt_start) * 1000, 1)})
                record.update({"successful_model": model, "status": "SUCCESS",
                               "latency_ms": round((time.perf_counter() - started) * 1000, 1)})
                return suggestion, record
            except Exception as exc:
                code = categorize(exc)
                record["attempts"].append({
                    "model": model, "error_code": code, "detail": scrub(exc)[:300],
                    "latency_ms": round((time.perf_counter() - attempt_start) * 1000, 1),
                })
                logger.warning("LLM attempt failed [request=%s model=%s code=%s]: %s",
                               record["request_id"], model, code, scrub(exc)[:300])
                if code == "AUTH_ERROR":
                    break

        record["latency_ms"] = round((time.perf_counter() - started) * 1000, 1)
        codes = [a["error_code"] for a in record["attempts"]]
        record["error_code"] = "AUTH_ERROR" if "AUTH_ERROR" in codes else (codes[-1] if codes else "CONNECTION_ERROR")
        raise LLMTargetServiceError("LLM_UNAVAILABLE", record, {"reasons": sorted(set(codes))})

    def health_check(self):

        started = time.perf_counter()
        try:
            self.client.chat.completions.create(
                model=self.models[0], messages=[{"role": "user", "content": "Reply with OK"}],
                max_tokens=2, temperature=0,
            )
            return {"status": "OK", "model": self.models[0],
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
        except Exception as exc:  # noqa: BLE001
            return {"status": "ERROR", "error_code": categorize(exc), "model": self.models[0],
                    "latency_ms": round((time.perf_counter() - started) * 1000, 1)}
