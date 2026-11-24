import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

class WorkspaceCreateRequest(BaseModel):
    """Schema for workspace creation request."""
    
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(min_length=2, max_length=120)
    slug: str = Field(min_length=2, max_length=120)
    
    @field_validator("slug", mode="after")
    @classmethod 
    def validate_slug(cls, v: str) -> str:
        """Validate the slug format."""
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("Slug must be lowercase letters, numbers, and hyphens only.")
        return v
    
class WorkspaceResponse(BaseModel):
    """Schema for workspace response."""
    
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    slug: str
    owner_id: uuid.UUID
    created_at: datetime
    
