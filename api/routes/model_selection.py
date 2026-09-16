from fastapi import (APIRouter,UploadFile,File,Form)
import json
import tempfile
import logging
from ml_engine.model_selection.application.model_selection_application import (ModelSelectionApplication)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS,CLUSTERING_ALGORITHMS)
from api.schemas.model_selection_response_schema import (ModelSelectionAPIResponse
)


logger = logging.getLogger(__name__)


router = APIRouter()


application = ModelSelectionApplication()



@router.post(
    "/model-selection",
    response_model=ModelSelectionAPIResponse
)
def select_model(

        file: UploadFile = File(...),

        problem_type: str = Form(...),

        target: str = Form(""),

        preferences: str = Form(...)

):

    try:

        preferences = json.loads(
            preferences
        )


        if problem_type == "clustering":
            target = None


        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
        ) as temp_file:


            temp_file.write(
                file.file.read()
            )


            dataset_path = temp_file.name


        if problem_type == "classification":
            algorithms = CLASSIFICATION_ALGORITHMS


        elif problem_type == "clustering":
            algorithms = CLUSTERING_ALGORITHMS
            if preferences.get("cluster_count_known"):
                algorithms = {

                    name: config

                    for name, config in algorithms.items()

                    if name != "DBSCAN"

                }

        else:

            raise ValueError("Unsupported problem type")


        response = application.run(
            dataset_path,
            problem_type,
            target,
            preferences,
            algorithms
        )


        return ModelSelectionAPIResponse(
            success=True,
            data=response,
            error=None
        )


    except json.JSONDecodeError:

        return ModelSelectionAPIResponse(

            success=False,
            data=None,
            error={
                "code": "INVALID_PREFERENCES",
                "message": "Preferences format is invalid"
            }

        )



    except Exception as e:


        logger.exception(
            "Model selection failed"
        )


        return ModelSelectionAPIResponse(

            success=False,
            data=None,
            error={
                "code": "MODEL_SELECTION_ERROR",
                "message": str(e)
            }

        )




@router.post("/validate-target")
def validate_target(
    file: UploadFile = File(...),
    target: str = Form(...)
):

    import tempfile
    import pandas as pd


    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".xlsx"
    ) as temp:

        temp.write(
            file.file.read()
        )

        path = temp.name


    df = pd.read_excel(path)



    if target not in df.columns:

        return {
            "success":False,
            "error":"Target پیدا نشد"
        }


    classes = (
        df[target]
        .value_counts()
    )


    if len(classes) < 2:

        return {
            "success":False,
            "error":
            "Target باید حداقل دو کلاس داشته باشد"
        }



    if classes.min() < 2:

        return {
            "success":False,
            "error":
            "بعضی کلاس‌های این Target فقط یک نمونه دارند و برای Classification مناسب نیستند"
        }


    return {
        "success":True
    }