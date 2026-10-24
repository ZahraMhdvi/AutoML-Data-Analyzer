CLASSIFICATION_ALGORITHMS = {


    "Logistic Regression": {

        "type": "classification",

        "strengths": [
            "fast",
            "interpretable",
            "small_dataset",
            "linear_relationship"
        ],


        "weaknesses": [
            "complex_patterns"
        ]
    },



    "Decision Tree": {

        "type": "classification",

        "strengths": [
            "interpretable",
            "fast",
            "handles_non_linear"
        ],


        "weaknesses": [
            "overfitting"
        ]
    },



    "Random Forest": {

        "type": "classification",

        "strengths": [
            "high_accuracy",
            "handles_noise",
            "non_linear",
            "mixed_features"
        ],


        "weaknesses": [
            "less_interpretable"
        ]
    },



    "XGBoost": {

        "type": "classification",

        "strengths": [
            "very_high_accuracy",
            "complex_patterns",
            "large_dataset",
            "handles_noise"
        ],


        "weaknesses": [
            "less_interpretable",
            "slower_training"
        ]
    },



    "SVM": {

        "type": "classification",

        "strengths": [
            "small_dataset",
            "high_dimension",
            "complex_boundaries"
        ],


        "weaknesses": [
            "large_dataset"
        ]
    },



    "KNN": {

        "type": "classification",

        "strengths": [
            "simple",
            "small_dataset",
            "local_patterns"
        ],


        "weaknesses": [
            "slow_prediction",
            "large_dataset"
        ]
    }

}




CLUSTERING_ALGORITHMS = {


    "KMeans": {

        "type": "clustering",

        "strengths": [
            "known_clusters",
            "fast",
            "numeric_features"
        ],


        "weaknesses": [
            "sensitive_to_noise",
            "requires_cluster_number"
        ]
    },



    "DBSCAN": {

        "type": "clustering",

        "strengths": [
            "unknown_clusters",
            "handles_noise",
            "irregular_shapes"
        ],


        "weaknesses": [
            "parameter_sensitive"
        ]
    },



    "Agglomerative Clustering": {

        "type": "clustering",

        "strengths": [
            "small_dataset",
            "hierarchical_analysis"
        ],


        "weaknesses": [
            "slow_for_large_dataset"
        ]
    }

}



SVM_MAX_ROWS = 20000
KNN_MAX_ROWS = 50000
AGGLOMERATIVE_MAX_ROWS = 10000


def eligibility(algorithm, problem_type, rows, preferences=None):


    preferences = preferences or {}

    if problem_type == "classification":
        if algorithm == "SVM" and rows > SVM_MAX_ROWS:
            return "SVM_TOO_MANY_ROWS"
        if algorithm == "KNN" and rows > KNN_MAX_ROWS:
            return "KNN_TOO_MANY_ROWS"
        if algorithm == "XGBoost":
            try:
                import xgboost  # noqa: F401
            except Exception:
                return "LIBRARY_NOT_INSTALLED"
        return None

    if problem_type == "clustering":
        if algorithm == "DBSCAN" and preferences.get("cluster_count_known"):
            return "DBSCAN_CANNOT_FIX_CLUSTER_COUNT"
        if algorithm == "Agglomerative Clustering" and rows > AGGLOMERATIVE_MAX_ROWS:
            return "AGGLOMERATIVE_TOO_MANY_ROWS"
        return None

    return "UNSUPPORTED_PROBLEM_TYPE"
