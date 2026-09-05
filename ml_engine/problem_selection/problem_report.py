from dataclasses import dataclass



@dataclass
class ProblemRecommendation:


    problem_type: str

    available: bool

    score: int

    priority: int

    reasons: list