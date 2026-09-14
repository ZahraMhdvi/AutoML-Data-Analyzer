from fastapi import APIRouter, UploadFile, File, Form
import tempfile
import pandas as pd


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

        target: str = Form("")

):

    try:


        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
        ) as temp:


            temp.write(
                file.file.read()
            )

            path = temp.name



        df = pd.read_excel(
            path
        )


        pipeline = PreprocessingPipeline(

            df,

            problem_type,

            target if target else None

        )


        processed = pipeline.process()



        result = execution_service.execute(

            algorithm,

            processed["dataframe"],

            processed["target"],

            problem_type

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