# GuidML – A Guided Low-Code AutoML Framework for Tabular Classification and Clustering

A low-code web application for non-expert users: upload an Excel/CSV dataset, get an
explainable recommendation of the analysis type (classification or clustering), resolve
the target (observed, user-selected or LLM-assisted pseudo-target), rank compatible
algorithms with a bounded Compatibility Score, and inspect results in a fully bilingual
(English / Persian) dashboard. Every dataset is a **project** with cumulative **versions**.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
# source .venv/bin/activate       # macOS / Linux
pip install -r requirements.txt
cp .env .env              # optional: add OPENROUTER_API_KEY for LLM pseudo-targets
python run.py                     # http://127.0.0.1:8000  (API docs: /docs)
```

Language: use the **EN / فا** switch in the header. The choice is stored in the browser
and on the user account (`PATCH /api/auth/me/preferences`).


## Tests

```bash
python -m pytest -q          # 50 tests
```


## Data storage

`storage/app.db` (users, projects, versions, results, LLM call log) and
`storage/projects/<id>/batch_<n>.*`. Existing databases are migrated automatically.
Set `APP_DATA_DIR` to store data elsewhere.
