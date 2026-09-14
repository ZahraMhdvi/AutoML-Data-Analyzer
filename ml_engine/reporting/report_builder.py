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


            "type":
                "classification",


            "metrics":
                metrics,


            "charts":[

                {
                    "type":"bar",
                    "title":"Model Performance",
                    "data":metrics
                },

                {
                    "type":"confusion_matrix"
                }

            ]

        }



    def _clustering_report(self,result):

        metrics = result["metrics"]

        return {

            "algorithm":
                result["algorithm"],


            "type":
                "clustering",


            "metrics":
                metrics,


            "charts":[

                {
                    "type":"cluster_distribution"
                },

                {
                    "type":"scatter"
                }

            ]

        }