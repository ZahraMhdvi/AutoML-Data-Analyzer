from dataclasses import dataclass
from typing import List
from ml_engine.response.recommendation_response import (RecommendationResponse)


@dataclass
class ModelSelectionResponse:


    problem_type: str

    target: str

    recommendations: List[RecommendationResponse]