from pydantic import BaseModel, Field


class CompanyControl(BaseModel):
    control_id: str
    title: str
    department: str
    description: str
    keywords: list[str] = Field(default_factory=list)
