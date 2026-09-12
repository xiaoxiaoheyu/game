from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Theme:
    board_color: str = "#d9a45b"
    line_color: str = "#38230f"
    black_color: str = "#181818"
    white_color: str = "#f5f5f0"
    background_color: str = "#17212b"
    panel_color: str = "#22303c"
    text_color: str = "#f4f4f4"
    accent_color: str = "#e4b65b"
    black_image: str = ""
    white_image: str = ""
    board_image: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "Theme":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)

