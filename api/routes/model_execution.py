from fastapi import APIRouter, UploadFile, File, Form
import json
import logging

from ml_engine.model_execution.runner import (
    run_model_on_dataframe,
    ModelRunError,
)

from api.core.datasets import read_uploaded_dataframe

from api.schemas.model_execution_response_schema import (
    ModelExecutionResponse
)


router = APIRouter()

logger = logging.getLogger(__name__)


@router.post(
    "/run-model",
    response_model=ModelExecutionResponse
)
def run_model(

        file: UploadFile = File(...),

        algorithm: str = Form(...),

        problem_type: str = Form(...),

        target: str = Form(""),

        preferences: str = Form("{}")

):


    try:

        preferences = json.loads(
            preferences
        )

        generated_dataset_id = (
            preferences.get(
                "generated_dataset_id"
            )
        )

        if generated_dataset_id:

            from api.routes.ai_target import (
                generated_datasets
            )

            if generated_dataset_id not in generated_datasets:

                raise ValueError(
                    "Generated dataset not found"
                )

            df = generated_datasets[
                generated_dataset_id
            ]

        else:

            df = read_uploaded_dataframe(file)

        result = run_model_on_dataframe(
            df,
            algorithm,
            problem_type,
            target or None,
            preferences
        )

        return ModelExecutionResponse(

            success=True,

            data=result,

            error=None

        )

    except ModelRunError as e:

        return ModelExecutionResponse(
            success=False,
            data=None,
            error={"code": "EXECUTION_ERROR", "message": str(e)}
        )

    except Exception as e:

        logger.exception("Model execution failed")

        return ModelExecutionResponse(

            success=False,

            data=None,

            error={

                "code":
                    "EXECUTION_ERROR",

                "message":
                    str(e)

            }

        )
