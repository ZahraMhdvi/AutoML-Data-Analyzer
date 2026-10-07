import json
import logging
import os
import re

import openai
from dotenv import load_dotenv
from openai import OpenAI

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


REQUEST_TIMEOUT = float(os.getenv("OPENROUTER_TIMEOUT", "45"))

SYSTEM_PROMPT = (
    "You are a professional data scientist. "
    "You always reply with a single valid JSON object and nothing else. "
    "All text values inside the JSON must be written in Persian. "
    "Use simple Persian language suitable for non-technical users."
)


class LLMTargetServiceError(Exception):


    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details or []


def _describe_error(exc):


    if isinstance(exc, openai.AuthenticationError):
        return "کلید API نامعتبر است یا منقضی شده"

    if isinstance(exc, openai.PermissionDeniedError):
        return "دسترسی به این مدل مجاز نیست"

    if isinstance(exc, openai.NotFoundError):
        return "این مدل دیگر به‌صورت رایگان در دسترس نیست"

    if isinstance(exc, openai.RateLimitError):
        return "محدودیت تعداد درخواست مدل رایگان پر شده است"

    if isinstance(exc, openai.APITimeoutError):
        return "مدل در زمان مجاز پاسخ نداد"

    if isinstance(exc, openai.APIConnectionError):
        return "اتصال به سرویس OpenRouter برقرار نشد"

    if isinstance(exc, openai.APIStatusError):
        return f"سرویس با خطای {exc.status_code} پاسخ داد"

    return "پاسخ مدل قابل استفاده نبود"


class LLMTargetService:

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise LLMTargetServiceError(
                "کلید OPENROUTER_API_KEY در فایل .env تنظیم نشده است."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            timeout=REQUEST_TIMEOUT,

            max_retries=0,
        )

        primary_model = (
            os.getenv("OPENROUTER_MODEL", "").strip()
            or DEFAULT_PRIMARY_MODEL
        )

        configured_fallbacks = [
            model.strip()
            for model in os.getenv("OPENROUTER_FALLBACK_MODELS", "").split(",")
            if model.strip()
        ]

        fallback_models = configured_fallbacks or DEFAULT_FALLBACK_MODELS

        self.models = []

        for model in [primary_model] + fallback_models + ["openrouter/free"]:
            if model not in self.models:
                self.models.append(model)

    def _build_prompt(self, dataset_profile):
        return f"""
You are an expert machine learning engineer.

Your task is to design a classification target for a dataset that does not
already have an obvious target column.

Analyze the dataset information below and decide which existing numeric or
categorical features should be combined into a new, meaningful target.

Rules:
- Ignore identifier columns.
- Do not invent a column name that already exists in the dataset unless it is
  the new generated target itself.
- Choose 2 to 6 important existing columns from "columns" as important_features.
- Only choose columns that appear in the "columns" list below.
- Create a target that would produce roughly balanced classes.
- All explanations and text fields must be written in Persian.
- The "reason" field must be a clear Persian explanation understandable for a normal user.
- Do not use English sentences in the response.
- Return only a single valid JSON object, with no markdown, no code fences,
  and no extra commentary.

Dataset:
{json.dumps(dataset_profile, indent=2, ensure_ascii=False)}

Return exactly this JSON shape:

{{
    "target_name": "name_of_target",
    "classes": ["class1", "class2", "class3"],
    "important_features": ["feature1", "feature2"],
    "reason": "why this target makes sense"
}}
"""

    @staticmethod
    def _extract_json(text):
        if not text:
            raise ValueError("Empty response from model")

        cleaned = text.strip()

        fence_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```",
            cleaned,
            re.DOTALL,
        )

        if fence_match:
            cleaned = fence_match.group(1)
        else:
            start = cleaned.find("{")
            end = cleaned.rfind("}")

            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end + 1]

        return json.loads(cleaned)

    @staticmethod
    def _response_text(response):


        choices = getattr(response, "choices", None)

        if not choices:
            error = getattr(response, "error", None)
            raise ValueError(f"No choices in response (error: {error})")

        message = getattr(choices[0], "message", None)

        if message is None:
            raise ValueError("Response has no message")

        content = getattr(message, "content", None)

        if not content:
            # Reasoning models may put everything in the "reasoning" field
            # and leave "content" empty.
            content = getattr(message, "reasoning", None)

        if not content:
            raise ValueError("Empty response from model")

        return content

    @staticmethod
    def _validate(result, dataset_profile):
        if not isinstance(result, dict):
            raise ValueError("Model response is not a JSON object")

        required_keys = (
            "target_name",
            "classes",
            "important_features",
            "reason",
        )

        missing = [
            key
            for key in required_keys
            if key not in result
        ]

        if missing:
            raise ValueError(
                f"Model response missing keys: {', '.join(missing)}"
            )

        if not isinstance(result["important_features"], list):
            raise ValueError("important_features is not a list")

        available_columns = set(
            dataset_profile.get("columns", [])
        )

        valid_features = [
            feature
            for feature in result["important_features"]
            if feature in available_columns
        ]

        if not valid_features:
            raise ValueError(
                "Model did not select any valid existing columns"
            )

        result["important_features"] = valid_features
        result["method"] = "ai"

        return result

    def generate_target_definition(self, dataset_profile):
        prompt = self._build_prompt(dataset_profile)

        details = []
        reasons = []

        for model in self.models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.2,
                    extra_headers={
                        "HTTP-Referer": "http://localhost",
                        "X-Title": "AutoML Data Analyzer",
                    },
                )

                result = self._extract_json(self._response_text(response))

                definition = self._validate(result, dataset_profile)
                definition["model"] = model

                return definition

            except Exception as exc:
                details.append(f"{model}: {exc}")
                reasons.append(f"{model}: {_describe_error(exc)}")
                logger.warning("AI target generation failed with %s: %s", model, exc)


                if isinstance(exc, openai.AuthenticationError):
                    break

                continue

        raise LLMTargetServiceError(
            "هیچ‌کدام از مدل‌های هوش مصنوعی پاسخ قابل استفاده‌ای نداد ("
            + "؛ ".join(reasons)
            + ")",
            details,
        )
