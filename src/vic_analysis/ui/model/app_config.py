from pathlib import Path
from typing import Self

from pydantic import BaseModel


class AppConfig(BaseModel):
    home_directory: Path | None = None
    colormap: str | None = None
    starting_image: Path | None = None

    def to_json(self, save_directory: Path | str, save_name: str) -> None:
        save_fp = Path(save_directory, save_name).with_suffix(".json")
        with open(save_fp, "w") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def from_json(cls, json_path: Path | str) -> Self:
        with open(json_path, "r") as f:
            return cls.model_validate_json(f.read())
