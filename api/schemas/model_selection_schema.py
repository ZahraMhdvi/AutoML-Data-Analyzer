from pydantic import BaseModel
from typing import Optional


class UserPreferenceRequest(BaseModel):

    main_goal: Optional[str] = None
    data_growth: Optional[str] = None
    feature_dimension: Optional[str] = None
    noise_presence: Optional[str] = None