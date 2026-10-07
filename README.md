# AutoML Data Analyzer

A low-code / no-code web app: upload an Excel dataset, the system recommends the
analysis type (Classification / Clustering), the target column and the best
algorithms, and shows the results in a dashboard. Users have accounts; every
dataset is a **project** with its own dashboard and a history of **versions
(branches)** when new records are added.

## Run

From the project folder (the one that contains `api/`, `frontend/`, `ml_engine/`):

```bash
# 1. create / activate a virtual environment
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux

# 2. install dependencies (once)
pip install -r requirements.txt

# 3. start the server
python run.py
#   or: python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000** in the browser. The backend serves the web page
and the API on the same address and port, so Live Server is not needed.

* Default address: `127.0.0.1` (this computer only), port `8000`.
* Other port: `python run.py --port 8080`.
* Other computers on the same network: `python run.py --host 0.0.0.0`, then
  open `http://<this-computer-IP>:8000`.
* API documentation: http://127.0.0.1:8000/docs

The optional AI target generation needs `OPENROUTER_API_KEY` in `.env`.

## Data storage

Everything is saved in the `storage/` folder (created automatically):
`storage/app.db` (users, projects, versions, results) and
`storage/projects/<id>/batch_<n>.xlsx` (uploaded files). Delete the folder to
start from scratch. Set `APP_DATA_DIR` to store it elsewhere.

## Tests

```bash
python -m pytest tests/test_projects_api.py -q
```
