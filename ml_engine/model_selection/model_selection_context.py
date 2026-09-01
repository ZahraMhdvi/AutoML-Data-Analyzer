from dataclasses import dataclass
from typing import Optional



@dataclass
class ModelSelectionContext:


    problem_type: str


    profile: dict


    columns: dict


    target: Optional[str]


    clean_data_shape: dict


    user_preferences: dict