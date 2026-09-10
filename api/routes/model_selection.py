from fastapi import (APIRouter,UploadFile,File,Form)
import json
import tempfile
from ml_engine.model_selection.application.model_selection_application import (ModelSelectionApplication)


from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)

router = APIRouter()
application = ModelSelectionApplication()



@router.post("/model-selection")
def select_model(

        file: UploadFile = File(...),
        problem_type: str = Form(...),
        target: str = Form(...),
        preferences: str = Form(...)
):


    preferences = json.loads(
        preferences
    )
    with tempfile.NamedTemporaryFile(delete=False,suffix=".xlsx") as temp_file:
        temp_file.write(file.file.read())
        dataset_path = temp_file.name
    response = application.run(
        dataset_path,
        problem_type,
        target,
        preferences,
        CLASSIFICATION_ALGORITHMS

    )


    return response