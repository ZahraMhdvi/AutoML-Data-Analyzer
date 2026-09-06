from ml_engine.model_selection.user_answer_handler import (UserAnswerHandler)


handler = UserAnswerHandler()
answers = {

    "main_goal": "accuracy",

    "data_growth": "static_data",

    "feature_dimension": "normal_dimension",

    "noise_presence": "has_noise"

}


preferences = handler.create_preferences(
    answers,
    "classification")

print(preferences)