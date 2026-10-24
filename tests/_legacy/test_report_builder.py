from ml_engine.reporting.report_builder import ReportBuilder



def test_classification_report():


    builder = ReportBuilder()


    result = {

        "algorithm":
            "Random Forest",

        "metrics": {

            "accuracy":0.9,

            "f1":0.85

        }

    }


    report = builder.build(result,"classification")

    assert report["problem_type"] == "classification"
    assert len(report["charts"]) > 0



def test_clustering_report():

    builder = ReportBuilder()

    result = {

        "algorithm":
            "DBSCAN",

        "metrics": {

            "number_of_clusters":4,

            "silhouette_score":0.6

        }

    }


    report = builder.build(
        result,
        "clustering"
    )


    assert report["problem_type"] == "clustering"