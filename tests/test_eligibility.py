from ml_engine.dataset_loader import DatasetLoader
from ml_engine.column_analyzer import ColumnAnalyzer
from ml_engine.target_detector import TargetDetector
from ml_engine.eligibility import EligibilityChecker


def test_classification_without_target_requires_generation():

    loader = DatasetLoader()

    df = loader.load_excel(
        "data/clustering_customer_dataset.xlsx"
    )


    column_analyzer = ColumnAnalyzer(df)

    column_analysis = (
        column_analyzer.analyze()
    )


    target_detector = TargetDetector(
        df,
        column_analysis
    )

    targets = target_detector.detect()


    checker = EligibilityChecker(
        df,
        column_analysis,
        targets
    )

    result = checker.evaluate()

    classification = (
        result["classification"]
    )


    assert targets == []

    assert classification["available"] is True

    assert (
        classification[
            "requires_target_generation"
        ]
        is True
    )

    assert (
        classification[
            "target_candidates"
        ]
        == []
    )