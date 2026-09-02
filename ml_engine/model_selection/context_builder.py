from ml_engine.model_selection.model_selection_context import (ModelSelectionContext)


class ModelSelectionContextBuilder:


    def build(self,analysis_result,clean_dataframe,user_preferences):


        problem_type = self._detect_problem_type(analysis_result["eligibility"])
        target = self._extract_target(analysis_result["targets"])


        clean_data_shape = {

            "rows":
                clean_dataframe.shape[0],

            "columns":
                clean_dataframe.shape[1]

        }


        return ModelSelectionContext(
            problem_type=problem_type,
            profile=analysis_result["profile"],
            columns=analysis_result["columns"],
            target=target,
            clean_data_shape=clean_data_shape,
            user_preferences=user_preferences
        )



    def _detect_problem_type(self,eligibility):


        if eligibility["classification"]["available"]:
            return "classification"



        if eligibility["clustering"]["available"]:
            return "clustering"

        return "unknown"



    def _extract_target(self, targets):
        if len(targets) == 0:
            return None

        return targets[0]["column"]