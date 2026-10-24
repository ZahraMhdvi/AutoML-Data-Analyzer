

class ReportBuilder:

    def build(self, execution_result, problem_type):
        metrics = execution_result["metrics"]
        if problem_type == "classification":
            return {
                "algorithm": execution_result["algorithm"],
                "problem_type": "classification",
                "summary": {"main_metric": "macro_f1", "value": metrics.get("macro_f1")},
                "charts": [{"type": "metric_bar"}, {"type": "confusion_matrix"}, {"type": "permutation_importance"}],
            }
        if problem_type == "clustering":
            return {
                "algorithm": execution_result["algorithm"],
                "problem_type": "clustering",
                "summary": {"clusters": metrics.get("cluster_count")},
                "charts": [{"type": "cluster_distribution"}, {"type": "scatter"}],
            }
        raise ValueError("Unsupported problem type")
