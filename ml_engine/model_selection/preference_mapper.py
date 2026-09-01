from ml_engine.model_selection.preference_schema import UserPreferences

def map_classification_preferences(preferences: UserPreferences):

    mapped_preferences = {
        "preferred_accuracy": False,
        "preferred_speed": False,
        "preferred_interpretability": False,
        "needs_noise_handling": False,
        "needs_high_dimension_support": False,
        "needs_continuous_learning": False
    }


    if preferences.main_goal == "accuracy":

        mapped_preferences["preferred_accuracy"] = True


    elif preferences.main_goal == "speed":

        mapped_preferences["preferred_speed"] = True


    elif preferences.main_goal == "interpretability":

        mapped_preferences["preferred_interpretability"] = True


    if preferences.data_growth == "continuous_data":
        mapped_preferences["needs_continuous_learning"] = True


    if preferences.feature_dimension == "high_dimension":
        mapped_preferences["needs_high_dimension_support"] = True


    if preferences.noise_presence == "has_noise":
        mapped_preferences["needs_noise_handling"] = True


    return mapped_preferences


def map_clustering_preferences(preferences: UserPreferences):


    mapped_preferences = {
        "needs_known_clusters": False,
        "needs_unknown_clusters": False,
        "needs_noise_handling": False,
        "needs_similar_clusters": False,
        "needs_irregular_clusters": False,
        "needs_hierarchy": False

    }



    if preferences.cluster_count_known == "known_clusters":

        mapped_preferences["needs_known_clusters"] = True

    elif preferences.cluster_count_known == "unknown_clusters":

        mapped_preferences["needs_unknown_clusters"] = True

    if preferences.noise_presence == "has_noise":

        mapped_preferences["needs_noise_handling"] = True

    if preferences.cluster_shape == "similar_clusters":

        mapped_preferences["needs_similar_clusters"] = True

    elif preferences.cluster_shape == "irregular_clusters":

        mapped_preferences["needs_irregular_clusters"] = True

    if preferences.hierarchical_analysis == "need_hierarchy":

        mapped_preferences["needs_hierarchy"] = True

    return mapped_preferences