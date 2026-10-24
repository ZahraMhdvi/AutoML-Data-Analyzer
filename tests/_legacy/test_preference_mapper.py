from ml_engine.model_selection.preference_schema import UserPreferences

from ml_engine.model_selection.preference_mapper import (
    map_classification_preferences,
    map_clustering_preferences
)



classification_preferences = UserPreferences(
    main_goal="accuracy",
    data_growth="continuous_data",
    feature_dimension="high_dimension",
    noise_presence="has_noise"
)


print(map_classification_preferences(classification_preferences))



clustering_preferences = UserPreferences(
    cluster_count_known="unknown_clusters",
    noise_presence="has_noise",
    cluster_shape="irregular_clusters",
    hierarchical_analysis="need_hierarchy"

)


print(map_clustering_preferences(clustering_preferences))