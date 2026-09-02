from ml_engine.model_selection.scoring_config import (CLASSIFICATION_SCORING_CONFIG,CLUSTERING_SCORING_CONFIG)

class CompatibilityScorer:

    def score(self,algorithm,dataset_features,problem_type):

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



        max_score = config["weights"]["dataset_compatibility"]


        active_features = [key for key, value in dataset_features.items() if value is True]

        if not active_features:

            return {

                "score":0,
                "matched":[],
                "unmatched":[]

            }



        matched = []
        unmatched = []


        for feature in active_features:

            if feature in algorithm["strengths"]:
                matched.append(feature)

            else:
                unmatched.append(feature)

        score = (len(matched) / len(active_features)) * max_score

        return {
            "score": round(score),
            "matched": matched,
            "unmatched": unmatched
        }