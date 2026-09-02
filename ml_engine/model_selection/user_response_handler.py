from ml_engine.model_selection.preference_schema import (UserPreferences)

class UserResponseHandler:

    def create_preferences(self,answers: dict) -> UserPreferences:

        return UserPreferences(
            main_goal=answers.get("main_goal"),
            data_growth=answers.get("data_growth"),
            feature_dimension=answers.get("feature_dimension"),
            noise_presence=answers.get("noise_presence"),
            cluster_count_known=answers.get("cluster_count_known"),
            cluster_shape=answers.get("cluster_shape"),
            hierarchical_analysis=answers.get("hierarchical_analysis" )

        )