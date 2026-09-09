from fastapi.testclient import TestClient
from api.main import app
client = TestClient(app)

def test_model_selection_api():

    response = client.post("/model-selection",
        json={
            "dataset_path": "data/customer_dataset.xlsx",
            "problem_type": "classification",
            "target": "Churn",
            "preferences": {
                "main_goal": "accuracy",
                "data_growth": "static_data",
                "feature_dimension": "normal_dimension",
                "noise_presence": "has_noise"
            }

        }

    )


    assert response.status_code == 200
    data = response.json()
    assert data["problem_type"] == "classification"
    assert data["target"] == "Churn"
    assert len(data["recommendations"]) > 0
    assert (data["recommendations"][0]["algorithm"]=="Random Forest")
    print(data)

    if __name__ == "__main__":
        test_model_selection_api()