from fastapi import APIRouter, UploadFile, File, Form
import tempfile
import pandas as pd
import json

from ml_engine.preprocessing.pipeline import (
    PreprocessingPipeline
)

from ml_engine.model_execution.executor import (
    ModelExecutionService
)

from api.schemas.model_execution_response_schema import (
    ModelExecutionResponse
)


router = APIRouter()


execution_service = ModelExecutionService()



@router.post(
    "/run-selected-model",
    response_model=ModelExecutionResponse
)
def run_selected_model(

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
        print(
            "GENERATED DATASET ID:",
            generated_dataset_id
        )



        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
        ) as temp:


            temp.write(
                file.file.read()
            )

            path = temp.name



        if generated_dataset_id:
            print(
                "USING AI GENERATED DATASET"
            )

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
            print(
                "COLUMNS:",
                df.columns.tolist()
            )



        else:


            df = pd.read_excel(
                path
            )


        pipeline = PreprocessingPipeline(

            df,

            problem_type,

            target if target else None

        )



        processed = (
            pipeline.process()
        )



        if problem_type == "classification":


            if processed["target"] is None:

                raise ValueError(
                    "Target missing"
                )



            counts = pd.Series(
                processed["target"]
            ).value_counts()



            if counts.min() < 2:

                raise ValueError(
                    "این Target برای Classification مناسب نیست چون بعضی کلاس‌ها نمونه کافی ندارند"
                )

        result = execution_service.execute(

            algorithm,

            processed["dataframe"],

            processed["target"],

            problem_type,

            preferences

        )


        return ModelExecutionResponse(

            success=True,

            data=result,

            error=None

        )


    except Exception as e:


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