from dataclasses import dataclass, field


@dataclass
class AlgorithmScoreResult:

    algorithm_name: str
    score: float
    matched: list
    unmatched: list
    reasons: list = field(default_factory=list)
    limitations: list = field(default_factory=list)
    raw: float = 0.0
    bound: float = 0.0
    evidence_considered: list = field(default_factory=list)
