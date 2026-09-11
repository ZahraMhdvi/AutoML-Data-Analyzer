from ml_engine.analysis.application.analysis_application import (AnalysisApplication)


def test_analysis_application():

    app = AnalysisApplication()
    result = app.analyze("data/customer_dataset.xlsx")
    print(result)
    assert "problem_recommendations" in result
    assert "target_candidates" in result