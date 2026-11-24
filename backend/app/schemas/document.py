import unicodedata
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

type DocSourceType = Literal["pdf", "docx", "markdown", "url"]


class DocumentCreateRequest(BaseModel):
    """DTO for creating a document."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(min_length=1, max_length=255, description="Title of the document.")
    source_type: DocSourceType = "markdown"
    content: str = Field(min_length=1, description="Content of the document.")
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("title", "content", mode="after")
    @classmethod
    def normalize_unicode(cls, value: str) -> str:
        """Normalize unicode characters to NFC form."""
        return unicodedata.normalize("NFC", value)

    @field_validator("tags", mode="after")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        """Normalize unicode characters in tags to NFC form. and deduplicate tags."""
        seen: set[str] = set()
        result: list[str] = []
        for tag in tags:
            clean = unicodedata.normalize("NFC", tag.lower())
            if clean and clean not in seen:
                seen.add(clean)
                result.append(clean)
        return result


class DocumentReadResponse(BaseModel):
    """DTO for reading a document."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    title: str
    source_type: DocSourceType
    content: str
    tags: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def word_count(self) -> int:
        return len(self.content.split())
