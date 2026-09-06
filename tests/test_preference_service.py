from ml_engine.model_selection.preference_service import (PreferenceService)
from ml_engine.model_selection.user_answer_handler import (UserAnswerHandler)


handler = UserAnswerHandler()
service = PreferenceService()

classification_answers = {

    "main_goal": "accuracy",

    "data_growth": "static_data",

    "feature_dimension": "normal_dimension",

    "noise_presence": "has_noise"

}

classification_preferences = handler.create_preferences(classification_answers,"classification")
mapped_classification = service.map_preferences(classification_preferences)
print("CLASSIFICATION")

print(mapped_classification)


clustering_answers = {


    "cluster_count_known": "unknown_clusters",

    "noise_presence": "has_noise",

    "cluster_shape": "irregular_clusters",

    "hierarchical_analysis": "need_hierarchy"

}

clustering_preferences = handler.create_preferences(

    clustering_answers,

    "clustering"

)


mapped_clustering = service.map_preferences(clustering_preferences)

print("\nCLUSTERING")
print(mapped_clustering)