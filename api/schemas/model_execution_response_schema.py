from pydantic import BaseModel
from typing import Optional, Dict, Any



class ModelExecutionResponse(BaseModel):

    success: bool

    data: Optional[Dict[str, Any]]

    error: Optional[Dict[str, str]]