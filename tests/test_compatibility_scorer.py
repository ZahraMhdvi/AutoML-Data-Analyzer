from ml_engine.model_selection.algorithm_registry import (CLASSIFICATION_ALGORITHMS)

from ml_engine.model_selection.dataset_feature_analyzer import (DatasetFeatureAnalyzer)

from ml_engine.model_selection.compatibility_scorer import (CompatibilityScorer)


context = build_real_context("data/customer_dataset.xlsx")


feature_analyzer = DatasetFeatureAnalyzer()
dataset_features = feature_analyzer.analyze(context)


algorithm = CLASSIFICATION_ALGORITHMS["Random Forest"]
scorer = CompatibilityScorer()
result = scorer.score(algorithm,dataset_features,context.problem_type)
print(dataset_features)
print(result)