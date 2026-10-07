

import io
import os

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import api.core.db as db
from api.main import app


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASSIFICATION_FILE = os.path.join(ROOT, "data", "customer_dataset.xlsx")
CLUSTERING_FILE = os.path.join(ROOT, "data", "clustering_customer_dataset.xlsx")


@pytest.fixture()
def client(tmp_path, monkeypatch):

    monkeypatch.setattr(db, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "app.db"))

    with TestClient(app) as test_client:
        yield test_client


def _xlsx(df):
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    return buffer.getvalue()


def _file(df, name="data.xlsx"):
    return {"file": (name, _xlsx(df), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}


def _signup(client, email="user@example.com"):
    response = client.post("/api/auth/signup", json={"name": "Ali", "email": email, "password": "secret123"})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}


def test_auth_flow(client):

    headers = _signup(client)

    assert client.get("/api/auth/me", headers=headers).json()["user"]["email"] == "user@example.com"


    assert client.post("/api/auth/signup", json={"name": "Xy", "email": "USER@example.com", "password": "secret123"}).status_code == 409


    assert client.post("/api/auth/login", json={"email": "user@example.com", "password": "nope"}).status_code == 401

    login = client.post("/api/auth/login", json={"email": "user@example.com", "password": "secret123"})
    assert login.status_code == 200

    client.post("/api/auth/logout", headers=headers)
    assert client.get("/api/auth/me", headers=headers).status_code == 401


    assert client.get("/api/projects").status_code == 401


def test_classification_project_with_branches(client):

    headers = _signup(client)
    df = pd.read_excel(CLASSIFICATION_FILE)

    created = client.post("/api/projects", headers=headers, files=_file(df.iloc[:600]), data={"name": "Churn"})
    assert created.status_code == 200, created.text
    project = created.json()["project"]
    pid = project["id"]

    assert project["status"] == "draft"
    assert project["analysis"]["recommended_targets"][0]["column"] == "Churn"


    chars = client.post(f"/api/projects/{pid}/characteristics", headers=headers,
                        json={"problem_type": "classification", "target": "Churn"}).json()
    assert chars["noise_presence"] in ("has_noise", "no_noise")
    assert chars["feature_dimension"] in ("high_dimension", "normal_dimension")

    prefs = {"main_goal": "accuracy", "data_growth": "continuous_data"}
    selection = client.post(f"/api/projects/{pid}/model-selection", headers=headers,
                            json={"problem_type": "classification", "target": "Churn", "preferences": prefs})
    assert selection.status_code == 200, selection.text
    body = selection.json()
    assert body["target"] == "Churn"
    assert body["data_characteristics"]["noise_presence"] == chars["noise_presence"]
    algorithm = body["recommendations"][0]["algorithm"]

    run = client.post(f"/api/projects/{pid}/run", headers=headers,
                      json={"problem_type": "classification", "target": "Churn", "preferences": prefs, "algorithm": algorithm})
    assert run.status_code == 200, run.text
    project = run.json()["project"]
    assert project["status"] == "ready"
    v1 = project["versions"][0]
    assert v1["status"] == "completed"
    assert set(v1["result"]["metrics"]["classes"]) == {"Yes", "No"}


    added = client.post(f"/api/projects/{pid}/versions", headers=headers, files=_file(df.iloc[600:800]))
    assert added.status_code == 200, added.text
    project = added.json()["project"]
    assert [v["total_rows"] for v in project["versions"]] == [600, 800]
    assert project["versions"][1]["rows_added"] == 200
    assert project["versions"][1]["summary"]["accuracy"] is not None


    bad = client.post(f"/api/projects/{pid}/versions", headers=headers, files=_file(df.iloc[800:].drop(columns=["City"])))
    assert bad.status_code == 400
    assert "City" in bad.json()["detail"]
    assert client.get(f"/api/projects/{pid}", headers=headers).json()["project"]["version_count"] == 2


    client.post(f"/api/projects/{pid}/versions", headers=headers, files=_file(df.iloc[800:]))
    assert client.get(f"/api/projects/{pid}", headers=headers).json()["project"]["total_rows"] == 1000
    undo = client.delete(f"/api/projects/{pid}/versions/3", headers=headers)
    assert undo.status_code == 200
    assert undo.json()["project"]["version_count"] == 2


    listing = client.get("/api/projects", headers=headers).json()["projects"]
    assert listing[0]["id"] == pid and listing[0]["version_count"] == 2

    other = _signup(client, "other@example.com")
    assert client.get(f"/api/projects/{pid}", headers=other).status_code == 404
    assert client.get("/api/projects", headers=other).json()["projects"] == []


    rerun = client.post(f"/api/projects/{pid}/run", headers=headers,
                        json={"problem_type": "classification", "target": "Churn", "preferences": prefs, "algorithm": "Decision Tree"})
    assert rerun.status_code == 200
    assert all(v["result"]["algorithm"] == "Decision Tree" for v in rerun.json()["project"]["versions"])

    assert client.delete(f"/api/projects/{pid}", headers=headers).status_code == 200
    assert client.get(f"/api/projects/{pid}", headers=headers).status_code == 404


def test_clustering_project_with_branches(client):

    headers = _signup(client)
    df = pd.read_excel(CLUSTERING_FILE)

    project = client.post("/api/projects", headers=headers, files=_file(df.iloc[:100])).json()["project"]
    pid = project["id"]
    assert project["analysis"]["target_required"] is True

    prefs = {"cluster_count_known": True, "cluster_count": 3, "cluster_shape": "unknown", "hierarchical_analysis": False}
    selection = client.post(f"/api/projects/{pid}/model-selection", headers=headers,
                            json={"problem_type": "clustering", "preferences": prefs}).json()
    names = [r["algorithm"] for r in selection["recommendations"]]
    assert "DBSCAN" not in names

    run = client.post(f"/api/projects/{pid}/run", headers=headers,
                      json={"problem_type": "clustering", "preferences": prefs, "algorithm": "KMeans"})
    assert run.status_code == 200, run.text
    assert run.json()["project"]["versions"][0]["summary"]["cluster_count"] == 3

    added = client.post(f"/api/projects/{pid}/versions", headers=headers, files=_file(df.iloc[100:]))
    assert added.status_code == 200, added.text
    assert added.json()["project"]["total_rows"] == 150


def test_ai_target_project(client, monkeypatch):

    class FakeLLM:
        def generate_target_definition(self, profile):
            return {
                "target_name": "value_tier",
                "classes": ["Low", "Medium", "High"],
                "important_features": ["Monthly_Spending", "Monthly_Visits"],
                "reason": "test",
            }

    from api.routes import ai_target
    monkeypatch.setattr(ai_target, "llm_service", FakeLLM())

    headers = _signup(client)
    df = pd.read_excel(CLUSTERING_FILE)

    pid = client.post("/api/projects", headers=headers, files=_file(df.iloc[:100])).json()["project"]["id"]

    generated = client.post(f"/api/projects/{pid}/ai-target", headers=headers)
    assert generated.status_code == 200, generated.text
    assert len(generated.json()["classes"]) == 3

    prefs = {"main_goal": "interpretability", "data_growth": "static_data"}
    run = client.post(f"/api/projects/{pid}/run", headers=headers,
                      json={"problem_type": "classification", "target_mode": "ai", "preferences": prefs, "algorithm": "Decision Tree"})
    assert run.status_code == 200, run.text
    project = run.json()["project"]
    assert project["config"]["target"] == "generated_target"
    assert project["config"]["ai_target"]["important_features"] == ["Monthly_Spending", "Monthly_Visits"]


    monkeypatch.setattr(ai_target, "llm_service", None)
    added = client.post(f"/api/projects/{pid}/versions", headers=headers, files=_file(df.iloc[100:]))
    assert added.status_code == 200, added.text


def test_manual_target_validation(client):

    headers = _signup(client)
    df = pd.read_excel(CLASSIFICATION_FILE).iloc[:300]

    pid = client.post("/api/projects", headers=headers, files=_file(df)).json()["project"]["id"]

    ok = client.post(f"/api/projects/{pid}/validate-target", headers=headers, json={"target": "Gender"})
    assert ok.status_code == 200

    bad = client.post(f"/api/projects/{pid}/validate-target", headers=headers, json={"target": "Customer_ID"})
    assert bad.status_code == 400


def test_rejects_non_excel(client):

    headers = _signup(client)

    response = client.post("/api/projects", headers=headers, files={"file": ("x.txt", b"hello", "text/plain")})
    assert response.status_code == 400
