from fastapi import APIRouter, UploadFile, File, Form
import json
import tempfile
import logging
from ml_engine.model_selection.application.model_selection_application import (ModelSelectionApplication)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from api.schemas.model_selection_response_schema import (ModelSelectionAPIResponse)


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

        target: str = Form(...),

        preferences: str = Form(...)

):

    try:

        preferences = json.loads(
            preferences
        )


        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
        ) as temp_file:


            temp_file.write(
                file.file.read()
            )


            dataset_path = temp_file.name



        response = application.run(

            dataset_path,

            problem_type,

            target,

            preferences,

            CLASSIFICATION_ALGORITHMS

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

            error={"code": "INVALID_PREFERENCES","message": "Preferences format is invalid"}

        )


    except Exception:


        logger.exception(
            "Model selection failed"
        )


        return ModelSelectionAPIResponse(

            success=False,

            data=None,

            error={

                "code": "MODEL_SELECTION_ERROR",

                "message": "Unable to process dataset"

            }

        )