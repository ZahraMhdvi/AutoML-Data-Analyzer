from dataclasses import dataclass, field
from typing import List, Optional

from ml_engine.response.recommendation_response import RecommendationResponse


@dataclass
class ModelSelectionResponse:

    problem_type: str
    target: Optional[str]
    recommendations: List[RecommendationResponse]
    excluded: List[dict] = field(default_factory=list)
    dataset_features: dict = field(default_factory=dict)
    score_semantics: str = "compatibility_prior_not_predicted_performance"
    score_formula: str = "CS = clip(50 + 50*raw/R, 0, 100); w_pref=+40/-15, w_data=+10/-10"
    data_characteristics: Optional[dict] = None
