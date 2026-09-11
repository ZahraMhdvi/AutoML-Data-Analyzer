from fastapi import FastAPI
from api.routes.model_selection import (router as model_selection_router)
from api.routes.analysis import (router as analysis_router)
app = FastAPI(title="AutoML Data Analyzer API")
app.include_router(model_selection_router)
app.include_router(analysis_router)