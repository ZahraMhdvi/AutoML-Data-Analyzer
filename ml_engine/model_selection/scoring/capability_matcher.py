class CapabilityMatcher:

    CAPABILITY_MAP = {

        "high_accuracy": [
            "high_accuracy",
            "very_high_accuracy"
        ],

        "handles_noise": [
            "handles_noise"
        ],

        "fast": [
            "fast"
        ],

        "interpretable": [
            "interpretable"
        ],

        "high_dimension": [
            "high_dimension"
        ],


        "known_clusters": [
            "known_clusters"
        ],

        "unknown_clusters": [
            "unknown_clusters"
        ],

        "numeric_features": [
            "numeric_features"
        ],

        "irregular_shapes": [
            "irregular_shapes"
        ],

        "small_dataset": [
            "small_dataset"
        ],

        "hierarchical_analysis": [
            "hierarchical_analysis"
        ]

    }


    def expand_preferences(self, preferences: dict):

        expanded = set()


        for key, value in preferences.items():

            if not value:
                continue


            if key in self.CAPABILITY_MAP:

                for capability in self.CAPABILITY_MAP[key]:

                    expanded.add(capability)


            else:

                expanded.add(key)


        return list(expanded)