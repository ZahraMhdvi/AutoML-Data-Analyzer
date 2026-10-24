from dataclasses import dataclass, field
from typing import List


@dataclass
class RecommendationResponse:

    algorithm: str
    score: float
    compatibility: str
    rank: int
    reasons: List[dict]
    limitations: List[dict]
    evidence_considered: List[dict] = field(default_factory=list)
    raw_points: float = 0.0
    max_points: float = 0.0
