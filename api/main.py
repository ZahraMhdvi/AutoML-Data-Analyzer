from fastapi import FastAPI
from api.routes.model_selection import (router as model_selection_router)
app = FastAPI(title="AutoML Data Analyzer API")
app.include_router(model_selection_router)