import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

SYSTEM_PROMPT = (
    "You are a professional data scientist. "
    "You always reply with a single valid JSON object and nothing else. "
    "All text values inside the JSON must be written in Persian. "
    "Use simple Persian language suitable for non-technical users."
)


class LLMTargetServiceError(Exception):
    """Raised when no configured model can produce a usable target definition."""


class LLMTargetService:

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise LLMTargetServiceError(
                "No API key configured. Set OPENROUTER_API_KEY in the .env file."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
        )

        primary_model = os.getenv(
            "OPENROUTER_MODEL",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
        )

        fallback_models = [
            model.strip()
            for model in os.getenv(
                "OPENROUTER_FALLBACK_MODELS",
                ""
            ).split(",")
            if model.strip()
        ]

        self.models = [primary_model] + [
            model
            for model in fallback_models
            if model != primary_model
        ]

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
    def _validate(result, dataset_profile):
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

        return result

    def generate_target_definition(self, dataset_profile):
        prompt = self._build_prompt(dataset_profile)

        errors = []

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

                result_text = response.choices[0].message.content

                result = self._extract_json(result_text)

                return self._validate(
                    result,
                    dataset_profile
                )

            except Exception as exc:
                errors.append(
                    f"{model}: {exc}"
                )
                continue

        raise LLMTargetServiceError(
            "AI target generation failed for all configured models. "
            + " | ".join(errors)
        )