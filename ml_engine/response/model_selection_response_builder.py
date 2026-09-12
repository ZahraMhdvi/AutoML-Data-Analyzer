from ml_engine.response.model_selection_response import (ModelSelectionResponse)
from ml_engine.response.response_builder import (ResponseBuilder)


class ModelSelectionResponseBuilder:


    def __init__(self):
        self.response_builder = ResponseBuilder()


    def build(self,context,score_results,algorithms):

        recommendations = (
            self.response_builder.build(
                score_results,
                algorithms
            )
        )

        target = context.target

        if context.problem_type == "clustering":
            target = None

        return ModelSelectionResponse(

            problem_type=context.problem_type,

            target=target,

            recommendations=recommendations

        )