from dataclasses import dataclass
from typing import List

@dataclass
class RecommendationResponse:

    algorithm: str

    score: int

    compatibility: str

    rank: int

    reasons: List[str]

    limitations: List[str]