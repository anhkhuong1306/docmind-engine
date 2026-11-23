from dataclasses import dataclass, field

# 1. Type alias
type MetadataDict = dict[str, str | int | float | bool]

# 2. Domain object
@dataclass(frozen=True, slots=True)
class TextChunk:
    """Chunking a paragraph and saving in the memory before embedding."""
    
    content: str
    chunk_index: int
    start_char: int
    end_char: int
    metadata: MetadataDict = field(default_factory=dict)
    
    @property
    def char_count(self) -> int:
        return len(self.content)
    
    