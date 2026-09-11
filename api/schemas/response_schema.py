from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ErrorResponse(BaseModel):

    code: str

    message: str



class APIResponse(BaseModel, Generic[T]):

    success: bool

    data: Optional[T] = None

    error: Optional[ErrorResponse] = None