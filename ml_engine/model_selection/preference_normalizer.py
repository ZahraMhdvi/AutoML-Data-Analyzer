class PreferenceNormalizer:


    def normalize(self,mapped_preferences: dict):

        normalized = {}
        for key, value in mapped_preferences.items():

            if value is True:
                normalized[key] = True


        replacements = {

            "preferred_accuracy":
                "high_accuracy",

            "preferred_speed":
                "fast",

            "preferred_interpretability":
                "interpretable",

            "needs_noise_handling":
                "handles_noise",

            "needs_high_dimension_support":
                "high_dimension",

            "needs_continuous_learning":
                "continuous_learning"

        }


        final_preferences = {}
        for key, value in normalized.items():

            if key in replacements:
                final_preferences[replacements[key]] = value

            else:

                final_preferences[key] = value


        return final_preferences