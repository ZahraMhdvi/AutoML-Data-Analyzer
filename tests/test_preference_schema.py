from ml_engine.model_selection.preference_schema import UserPreferences



preferences = UserPreferences(

    main_goal="accuracy",

    data_growth="continuous_data",

    feature_dimension="high_dimension",

    noise_presence="has_noise"

)



print(preferences)