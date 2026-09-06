from dataclasses import dataclass



@dataclass
class AlgorithmScoreResult:


    algorithm_name: str

    score: int

    matched: list

    unmatched: list