from fastapi import APIRouter, UploadFile, File
import tempfile
import logging
from ml_engine.analysis.application.analysis_application import (AnalysisApplication)
from api.schemas.analysis_schema import (AnalysisAPIResponse)


router = APIRouter()
logger = logging.getLogger(__name__)
application = AnalysisApplication()


@router.post("/analyze-dataset",response_model=AnalysisAPIResponse)
def analyze_dataset(
        file: UploadFile = File(...)
):

    try:

        with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
        ) as temp_file:


            temp_file.write(
                file.file.read()
            )


            dataset_path = temp_file.name



        result = application.analyze(
            dataset_path
        )


        return AnalysisAPIResponse(

            success=True,
            data=result,
            error=None

        )


    except Exception:

        logger.exception("Dataset analysis failed")

        return AnalysisAPIResponse(
            success=False,
            data=None,
            error={
                "code": "ANALYSIS_ERROR",
                "message": "Unable to analyze dataset"
            }

        )