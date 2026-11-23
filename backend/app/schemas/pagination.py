from pydantic import BaseModel, Field, computed_field

class PaginatedResponse[T](BaseModel):
    """Generic DTO for paginated responses."""
    
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1, default=1)
    page_size: int = Field(ge=1, le=100, default=20)
    
    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page * self.page_size < self.total
    
    