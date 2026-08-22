

class EligibilityChecker:

    def __init__(self,dataframe,column_analysis,target_candidates):
        self.dataframe = dataframe
        self.column_analysis = column_analysis
        self.target_candidates = target_candidates

    def get_feature_columns(self):

        features = []

        target_columns = [
            item["column"]
            for item in self.target_candidates
        ]

        for column, info in self.column_analysis.items():

            if column in target_columns:
                continue

            if info["semantic_type"] in [
                "numerical",
                "categorical"
            ]:
                features.append(column)

        return features




    def check_classification(self):

        if len(self.target_candidates) == 0:

            return {
                "available": False,
                "reason": "No target candidate found"
            }


        features = self.get_feature_columns()


        if len(features) == 0:

            return {
                "available": False,
                "reason": "No usable features found"
            }


        return {
            "available": True,
            "target_candidates": self.target_candidates,
            "features": features
        }



    def check_clustering(self):

        features = self.get_feature_columns()


        if len(features) == 0:

            return {
                "available": False,
                "reason": "No usable features found"
            }


        return {
            "available": True,
            "features": features
        }


    def evaluate(self):

        return {
            "classification":
                self.check_classification(),

            "clustering":
                self.check_clustering()
        }