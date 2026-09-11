from fastapi import FastAPI
from api.routes.model_selection import (router as model_selection_router)
from api.routes.analysis import (router as analysis_router)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)
app.include_router(model_selection_router)
app.include_router(analysis_router)