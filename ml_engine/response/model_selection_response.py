from dataclasses import dataclass
from typing import List, Optional

from ml_engine.response.recommendation_response import (
    RecommendationResponse
)


@dataclass
class ModelSelectionResponse:

    problem_type: str

    target: Optional[str]

    recommendations: List[RecommendationResponse]

    data_characteristics: Optional[dict] = None
