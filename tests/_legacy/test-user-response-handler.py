from ml_engine.model_selection.user_response_handler import (UserResponseHandler)

answers = {
    "main_goal": "accuracy",
    "data_growth": "static_data",
    "feature_dimension": "normal_dimension",
    "noise_presence": "has_noise"
}
handler = UserResponseHandler()
preferences = handler.create_preferences(answers)
print(preferences)