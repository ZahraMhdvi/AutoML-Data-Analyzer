from typing import Any
from pydantic import BaseModel


class ModelSelectionAPIResponse(BaseModel):

    success: bool

    data: Any

    error: dict | None = None