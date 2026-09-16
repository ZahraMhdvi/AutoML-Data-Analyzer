import pandas as pd



class TargetGenerator:


    def generate(
            self,
            dataframe,
            definition
    ):


        features = (
            definition["important_features"]
        )


        if len(features) == 0:

            raise ValueError(
                "No features selected"
            )


        score = (
            dataframe[features]
            .rank()
            .mean(axis=1)
        )


        dataframe["generated_target"] = pd.qcut(

            score,

            q=3,

            labels=[
                "Low",
                "Medium",
                "High"
            ]

        )


        return dataframe