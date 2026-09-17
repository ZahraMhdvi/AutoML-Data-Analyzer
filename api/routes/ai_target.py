from fastapi import APIRouter, UploadFile, File
import tempfile
import pandas as pd
import uuid

from ml_engine.ai.llm_target_service import (
    LLMTargetService,
    LLMTargetServiceError,
)

from ml_engine.ai.target_generator import (
    TargetGenerator
)

from ml_engine.column_analyzer import ColumnAnalyzer


router = APIRouter()


generated_datasets = {}


try:
    llm_service = LLMTargetService()
except LLMTargetServiceError:
    llm_service = None

target_generator = TargetGenerator()


def _build_dataset_profile(df):
    column_analysis = ColumnAnalyzer(df).analyze()

    columns_info = []

    for column, info in column_analysis.items():
        entry = {
            "name": column,
            "type": info["semantic_type"],
        }

        if info["semantic_type"] == "numerical":
            entry["mean"] = round(float(df[column].mean()), 4)
            entry["min"] = round(float(df[column].min()), 4)
            entry["max"] = round(float(df[column].max()), 4)
        elif info["semantic_type"] != "identifier":
            entry["sample_values"] = [
                str(value) for value in df[column].dropna().unique()[:5]
            ]

        columns_info.append(entry)

    return {
        "columns": list(df.columns),
        "columns_info": columns_info,
        "rows": len(df),
    }


@router.post(
    "/generate-target-with-ai"
)
def generate_target_with_ai(
        file: UploadFile = File(...)
):

    if llm_service is None:

        return {
            "success": False,
            "error": {
                "code": "AI_NOT_CONFIGURED",
                "message": "AI target generation is not configured. Set OPENROUTER_API_KEY in the .env file.",
            },
        }

    try:

        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
        ) as temp:

            temp.write(
                file.file.read()
            )

            path = temp.name

        df = pd.read_excel(path)

        if df.empty:
            raise ValueError("Dataset is empty")

        dataset_profile = _build_dataset_profile(df)

        definition = llm_service.generate_target_definition(dataset_profile)

        generated_df = target_generator.generate(df, definition)

        classes = sorted(generated_df["generated_target"].dropna().unique().tolist())

        dataset_id = str(uuid.uuid4())

        generated_datasets[dataset_id] = generated_df

        return {

            "success": True,

            "data": {

                "dataset_id": dataset_id,

                "target_column": "generated_target",

                "problem_type": "classification",

                "generated": True,

                "classes": classes,

                "important_features": definition["important_features"],

                "reason": definition["reason"]

            }

        }

    except LLMTargetServiceError as e:

        return {

            "success": False,

            "error": {

                "code": "AI_TARGET_ERROR",

                "message": str(e)

            }

        }

    except Exception as e:

        return {

            "success": False,

            "error": {

                "code": "AI_TARGET_ERROR",

                "message": str(e)

            }

        }
