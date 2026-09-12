from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Theme:
    board_color: str = "#f2cfa3"
    line_color: str = "#9b7057"
    black_color: str = "#181818"
    white_color: str = "#f5f5f0"
    background_color: str = "#fff7f2"
    panel_color: str = "#fffdf9"
    text_color: str = "#51464a"
    accent_color: str = "#f18a9b"
    secondary_color: str = "#8f7ccb"
    muted_text_color: str = "#8f7f84"
    shadow_color: str = "#decbd0"
    success_color: str = "#70bfa1"
    black_image: str = ""
    white_image: str = ""
    board_image: str = ""

    @classmethod
    def load(cls, path: str | Path) -> "Theme":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        known = {key: value for key, value in data.items() if key in cls.__dataclass_fields__}
        return cls(**known)
