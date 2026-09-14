class ReportBuilder:


    def build(self,execution_result,problem_type):


        if problem_type == "classification":
            return self._classification_report(execution_result)


        elif problem_type == "clustering":
            return self._clustering_report(execution_result)

        else:

            raise ValueError(
                "Unsupported problem type"
            )


    def _classification_report(self,result):

        metrics = result["metrics"]

        return {
            "algorithm":
                result["algorithm"],


            "problem_type":
                "classification",


            "summary": {

                "main_metric":
                    "accuracy",

                "value":
                    metrics.get(
                        "accuracy"
                    )

            },


            "metrics":
                metrics,


            "charts":[

                {
                    "type":
                        "metric_bar",

                    "title":
                        "Model Performance",

                    "data":
                        metrics

                },

                {
                    "type":
                        "confusion_matrix",

                    "title":
                        "Confusion Matrix",
                    "data":
                        metrics.get(
                            "confusion_matrix"
                        )

                }

            ]

        }



    def _clustering_report(self,result):

        metrics = result["metrics"]

        return {

            "algorithm":
                result["algorithm"],


            "problem_type":
                "clustering",


            "summary": {

                "clusters":
                    metrics.get(
                        "number_of_clusters"
                    )

            },


            "metrics":
                metrics,


            "charts":[

                {
                    "type":
                        "cluster_distribution",

                    "title":
                        "Cluster Sizes"

                },

                {
                    "type":
                        "scatter",

                    "title":
                        "Cluster Visualization"

                }

            ]

        }