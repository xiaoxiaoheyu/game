from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .constants import COLOR_NAMES
from .game import Game


def save_game(game: Game, directory: str = "logs") -> Path:
    path = Path(directory)
    path.mkdir(parents=True, exist_ok=True)
    output = path / f"game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    payload = {
        "board_size": 19,
        "win_length": 6,
        "black": game.players[1].name,
        "white": game.players[2].name,
        "status": game.status.value,
        "winner": COLOR_NAMES.get(game.winner, "和棋"),
        "turns": [record.as_dict() for record in game.records],
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output

