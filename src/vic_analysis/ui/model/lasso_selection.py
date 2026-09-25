from dataclasses import dataclass, field
from typing import Self
from uuid import UUID, uuid4

import numpy as np


@dataclass(frozen=True)
class LassoSelection:
    vertices: np.ndarray
    id: UUID = field(default_factory=uuid4)

    @classmethod
    def empty(cls) -> Self:
        return cls(np.zeros(0))
