from ml_engine.model_selection.preference_schema import (UserPreferences)

class UserAnswerHandler:

    def create_preferences(self,answers: dict,problem_type: str):

        preferences = UserPreferences()
        preferences.problem_type = problem_type
        for key, value in answers.items():

            if hasattr(preferences, key):
                setattr(preferences,key,value)

        return preferences