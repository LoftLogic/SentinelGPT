from pydantic import BaseModel


class Plan(BaseModel):
    script: str
