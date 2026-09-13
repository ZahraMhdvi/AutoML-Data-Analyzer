from ml_engine.model_selection.preference_schema import UserPreferences

def map_classification_preferences(preferences: UserPreferences):

    mapped_preferences = {
        "high_accuracy": False,
        "fast": False,
        "interpretable": False,
        "handles_noise": False,
        "high_dimension": False,
        "large_dataset": False
    }


    if preferences.main_goal == "accuracy":
        mapped_preferences["high_accuracy"] = True


    elif preferences.main_goal == "speed":
        mapped_preferences["fast"] = True


    elif preferences.main_goal == "interpretability":
        mapped_preferences["interpretable"] = True

    if preferences.data_growth == "continuous_data":
        mapped_preferences["large_dataset"] = True

    if preferences.feature_dimension == "high_dimension":
        mapped_preferences["high_dimension"] = True

    if preferences.noise_presence == "has_noise":
        mapped_preferences["handles_noise"] = True

    return mapped_preferences





def map_clustering_preferences(preferences: UserPreferences):

    mapped_preferences = {
        "known_clusters": False,
        "unknown_clusters": False,
        "handles_noise": False,
        "irregular_shapes": False,
        "hierarchical_analysis": False,
        "fast": False
    }


    if preferences.cluster_count_known is True:

        mapped_preferences["known_clusters"] = True


    elif preferences.cluster_count_known is False:

        mapped_preferences["unknown_clusters"] = True




    if preferences.noise_presence == "has_noise":

        mapped_preferences["handles_noise"] = True




    if preferences.cluster_shape == "irregular":

        mapped_preferences["irregular_shapes"] = True




    if preferences.hierarchical_analysis is True:

        mapped_preferences["hierarchical_analysis"] = True



    return mapped_preferences