from fastapi import APIRouter, UploadFile, File
import tempfile
import pandas as pd
import uuid

from ml_engine.ai.llm_target_service import (
    LLMTargetService
)

from ml_engine.ai.target_generator import (
    TargetGenerator
)


router = APIRouter()


generated_datasets = {}


llm_service = LLMTargetService()

target_generator = TargetGenerator()



@router.post(
    "/generate-target-with-ai"
)
def generate_target_with_ai(
        file: UploadFile = File(...)
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



        numeric_columns = list(

            df.select_dtypes(
                include=[
                    "int64",
                    "float64"
                ]
            ).columns

        )



        dataset_profile = {

            "columns":
                list(df.columns),


            "numeric_columns":
                numeric_columns,


            "rows":
                len(df)

        }



        definition = (
            llm_service
            .generate_target_definition(
                dataset_profile
            )
        )



        generated_df = (
            target_generator
            .generate(
                df,
                definition
            )
        )



        dataset_id = str(
            uuid.uuid4()
        )


        generated_datasets[dataset_id] = generated_df



        return {

            "success": True,

            "data": {

                "dataset_id":
                    dataset_id,


                "target_column":
                    "generated_target",


                "problem_type":
                    "classification",


                "generated":
                    True,


                "classes":
                    [
                        "Low",
                        "Medium",
                        "High"
                    ],


                "reason":
                    definition["reason"]

            }

        }



    except Exception as e:


        return {

            "success": False,

            "error": {

                "code":
                    "AI_TARGET_ERROR",


                "message":
                    str(e)

            }

        }