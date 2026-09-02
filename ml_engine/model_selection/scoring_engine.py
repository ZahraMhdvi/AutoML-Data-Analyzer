from ml_engine.model_selection.algorithm_registry import (
    CLASSIFICATION_ALGORITHMS,
    CLUSTERING_ALGORITHMS
)

class ScoringEngine:


    def recommend(self, context):

        if context.problem_type == "classification":
            algorithms = CLASSIFICATION_ALGORITHMS

        elif context.problem_type == "clustering":
            algorithms = CLUSTERING_ALGORITHMS

        else:
            return []



        results = []


        for name, algorithm in algorithms.items():

            score, reasons, warnings = self._score_algorithm(algorithm,context)
            results.append({
                "algorithm": name,
                "score": score,
                "reasons": reasons,
                "warnings": warnings
            })


        results.sort(key=lambda x: x["score"],reverse=True)
        return results


    def _score_algorithm(self,algorithm,context):
        score = 0
        reasons = []
        warnings = []

        strengths = algorithm["strengths"]
        weaknesses = algorithm["weaknesses"]

        for preference, value in context.user_preferences.items():


            if value is True and preference in strengths:

                score += 25

                reasons.append(f"الگوریتم با نیاز کاربر ({preference}) هماهنگ است")


        dataset_features = self._extract_dataset_features(context)
        for feature, value in dataset_features.items():

            if value and feature in strengths:
                score += 10
                reasons.append(f"برای ویژگی دیتاست ({feature}) مناسب است")


        for weakness in weaknesses:

            if weakness in context.user_preferences:
                if context.user_preferences[weakness] is True:
                    score -= 10
                    warnings.append(f"این الگوریتم مشکل {weakness} دارد")


        score = max(0,min(score,100))
        return score, reasons, warnings



    def _extract_dataset_features(self,context):
        features = {}
        rows = context.clean_data_shape["rows"]
        columns = context.clean_data_shape["columns"]
        features["small_dataset"] = rows < 1000
        features["large_dataset"] = rows > 10000
        features["high_dimension"] = columns > 50

        return features