from dataclasses import dataclass, field


@dataclass
class ProblemRecommendation:

    problem_type: str
    available: bool
    status: str
    priority: int
    evidence: list = field(default_factory=list)

    @property
    def reasons(self):
        return [item["code"] for item in self.evidence]
