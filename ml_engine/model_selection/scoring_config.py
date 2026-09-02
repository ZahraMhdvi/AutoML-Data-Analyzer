CLASSIFICATION_SCORING_CONFIG = {


    "weights": {

        "preference_match": 50,
        "dataset_compatibility": 30,
        "algorithm_characteristics": 20,
        "penalty": -20

    },


    "thresholds": {

        "small_dataset_max_rows": 1000,
        "large_dataset_min_rows": 10000,
        "high_dimension_min_features": 50

    }

}





CLUSTERING_SCORING_CONFIG = {


    "weights": {
        "preference_match": 50,
        "dataset_compatibility": 30,
        "algorithm_characteristics": 20,
        "penalty": -20

    },


    "thresholds": {

        "small_dataset_max_rows": 1000,
        "large_dataset_min_rows": 10000,
        "high_dimension_min_features": 50

    }

}