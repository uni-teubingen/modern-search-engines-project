from dataclasses import dataclass, field
from typing import List

@dataclass
class ResultDto():
    doc_id : int
    title: str
    url: str
    palmer_score: bool
    snippet: str
    score: float = 0  
