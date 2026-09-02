from ml_engine.model_selection.scoring_config import (CLASSIFICATION_SCORING_CONFIG,CLUSTERING_SCORING_CONFIG)


class PreferenceScorer:

    def score(self,algorithm,user_preferences,problem_type):

        if problem_type == "classification":
            config = CLASSIFICATION_SCORING_CONFIG

        elif problem_type == "clustering":
            config = CLUSTERING_SCORING_CONFIG

        else:
            return {
                "score": 0,
                "matched": [],
                "unmatched": []
            }


        max_score = config["weights"]["preference_match"]
        active_preferences = [key for key, value in user_preferences.items() if value is True]

        if not active_preferences:

            return {

                "score":0,
                "matched":[],
                "unmatched":[]

            }



        matched = []
        unmatched = []



        for preference in active_preferences:

            if preference in algorithm["strengths"]:
                matched.append(preference)

            else:
                unmatched.append(preference)

        score = (len(matched) / len(active_preferences)) * max_score

        return {
            "score": round(score),
            "matched": matched,
            "unmatched": unmatched
        }