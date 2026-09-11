from typing import List, Optional
from pydantic import BaseModel



class ProblemOptionSchema(BaseModel):

    problem_type: str
    available: bool
    score: int
    reasons: List[str]


class TargetCandidateSchema(BaseModel):

    name: str
    confidence: float


class DatasetInfoSchema(BaseModel):

    rows: int
    columns: int


class AnalysisDataSchema(BaseModel):

    dataset_info: DatasetInfoSchema
    problem_options: List[ProblemOptionSchema]
    target_candidates: List[TargetCandidateSchema]


class AnalysisAPIResponse(BaseModel):

    success: bool
    data: Optional[AnalysisDataSchema] = None
    error: Optional[dict] = None