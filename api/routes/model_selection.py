from fastapi import APIRouter
from api.schemas.model_selection_schema import (ModelSelectionRequest)
from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)
from ml_engine.model_selection.application.model_selection_application import ModelSelectionApplication

router = APIRouter()
application = ModelSelectionApplication()



@router.post("/model-selection")
def select_model(request: ModelSelectionRequest):


    response = application.run(
        request.dataset_path,
        request.problem_type,
        request.target,
        request.preferences.model_dump(),
        CLASSIFICATION_ALGORITHMS
    )

    return response