from fastapi.testclient import TestClient
from api.main import app
client = TestClient(app)

def test_model_selection_upload_api():


    with open(
        "data/customer_dataset.xlsx",
        "rb"
    ) as file:


        response = client.post(

            "/model-selection",

            files={
                "file": (
                    "customer_dataset.xlsx",
                    file,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            },

            data={

                "problem_type": "classification",

                "target": "Churn",

                "preferences": """
                {
                    "main_goal":"accuracy",
                    "data_growth":"static_data",
                    "feature_dimension":"normal_dimension",
                    "noise_presence":"has_noise"
                }
                """

            }

        )


    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True

    assert result["error"] is None

    assert result["data"]["problem_type"] == "classification"

    assert result["data"]["target"] == "Churn"

    assert (
            result["data"]["recommendations"][0]["algorithm"]
            ==
            "Random Forest"
    )


def test_model_selection_invalid_preferences():


    with open(
        "data/customer_dataset.xlsx",
        "rb"
    ) as file:


        response = client.post(

            "/model-selection",

            files={

                "file": (

                    "customer_dataset.xlsx",

                    file,

                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

                )

            },

            data={

                "problem_type": "classification",

                "target": "Churn",

                "preferences": "invalid-json"

            }

        )


    assert response.status_code == 200


    result = response.json()


    assert result["success"] is False


    assert result["data"] is None


    assert result["error"]["code"] == "INVALID_PREFERENCES"
