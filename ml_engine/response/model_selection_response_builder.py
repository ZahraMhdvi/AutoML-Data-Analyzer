from ml_engine.response.model_selection_response import ModelSelectionResponse
from ml_engine.response.response_builder import ResponseBuilder


class ModelSelectionResponseBuilder:

    def __init__(self):
        self.response_builder = ResponseBuilder()

    def build(self, context, score_results, algorithms, excluded=None, dataset_features=None):
        return ModelSelectionResponse(
            problem_type=context.problem_type,
            target=None if context.problem_type == "clustering" else context.target,
            recommendations=self.response_builder.build(score_results, algorithms),
            excluded=list(excluded or []),
            dataset_features=dict(dataset_features or {}),
        )
