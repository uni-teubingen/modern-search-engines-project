from dataclasses import dataclass, field
from typing import List

@dataclass
class ResultDto():
    title: str
    url: str
    palmer_score: bool
    snippet: str
