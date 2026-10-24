

from ml_engine.model_execution.runner import run_classification, run_clustering


class ModelExecutionService:

    def execute_raw(self, algorithm, df, problem_type, target=None, preferences=None, **kwargs):
        preferences = preferences or {}
        if problem_type == "classification":
            return run_classification(df, algorithm, {"type": "observed", "column": target}, **kwargs)
        return run_clustering(df, algorithm, preferences.get("cluster_count"), **kwargs)
