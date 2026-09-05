from dataclasses import dataclass
from typing import Optional


@dataclass
class UserPreferences:

    problem_type: Optional[str] = None
    
    main_goal: Optional[str] = None

    data_growth: Optional[str] = None

    feature_dimension: Optional[str] = None

    noise_presence: Optional[str] = None

    cluster_count_known: Optional[str] = None

    cluster_shape: Optional[str] = None

    hierarchical_analysis: Optional[str] = None