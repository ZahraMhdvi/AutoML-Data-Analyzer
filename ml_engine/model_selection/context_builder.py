from ml_engine.model_selection.model_selection_context import (
    ModelSelectionContext
)


class ModelSelectionContextBuilder:


    def build(self,analysis_result,clean_dataframe,user_preferences,problem_type):
        target = self._extract_target(analysis_result["targets"])
        processed_columns = {

            column: {

                "technical_type":
                    str(clean_dataframe[column].dtype)

            }

            for column in clean_dataframe.columns

        }


        return ModelSelectionContext(
            problem_type=problem_type,
            profile=analysis_result["profile"],
            raw_columns=analysis_result["columns"],
            processed_columns=processed_columns,
            target=target,
            clean_data_shape={
                "rows": clean_dataframe.shape[0],
                "columns": clean_dataframe.shape[1]

            },
            user_preferences=user_preferences

        )



    def _extract_target(self, targets):
        if len(targets) == 0:
            return None

        return targets[0]["column"]