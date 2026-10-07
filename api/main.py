import os
import uuid
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sklearn.cluster import KMeans

from api.core.db import init_db, ROOT_DIR
from api.routes.model_selection import (router as model_selection_router)
from api.routes.analysis import (router as analysis_router)
from api.routes import model_execution
from api.routes import ai_target
from api.routes import auth as auth_routes
from api.routes import projects as project_routes


generated_datasets = {}

FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")

@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield


app = FastAPI(title="AutoML Data Analyzer", lifespan=lifespan)


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

app.include_router(auth_routes.router)
app.include_router(project_routes.router)

app.include_router(model_selection_router)
app.include_router(analysis_router)
app.include_router(model_execution.router)
app.include_router(ai_target.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/generate-target-from-clusters")
async def generate_target_from_clusters(
    file: UploadFile = File(...)
):

    try:

        df = pd.read_excel(file.file)

        model = KMeans(
            n_clusters=3,
            random_state=42
        )

        labels = model.fit_predict(
            df.select_dtypes(
                include="number"
            )
        )

        df["generated_target"] = labels

        dataset_id = str(uuid.uuid4())

        generated_datasets[dataset_id] = df

        return {
            "success": True,
            "data": {

                "dataset_id": dataset_id,

                "target_column":
                    "generated_target",

                "problem_type":
                    "classification",

                "generated":
                    True,

                "classes":
                    list(
                        map(
                            int,
                            set(labels)
                        )
                    )
            }
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="frontend")
