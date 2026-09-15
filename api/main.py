from fastapi import FastAPI, File, UploadFile
from sklearn.cluster import KMeans
import pandas as pd
from api.routes.model_selection import (router as model_selection_router)
from api.routes.analysis import (router as analysis_router)
from fastapi.middleware.cors import CORSMiddleware
from api.routes import model_execution
import uuid

generated_datasets = {}
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
app.include_router(model_execution.router)
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
                "target_column": "generated_target",
                "classes": list(
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