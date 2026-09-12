from __future__ import annotations

import random
from abc import ABC, abstractmethod

from .board import Board, Position
from .constants import BLACK, BOARD_SIZE, EMPTY, opponent
from .rules import DIRECTIONS, line_length


class Player(ABC):
    def __init__(self, name: str):
        self.name = name
        self.color: int | None = None

    def on_game_start(self, color: int) -> None:
        self.color = color

    def on_opponent_turn(self, moves: list[Position]) -> None:
        """External adapters can use this hook to synchronize opponent positions."""

    @abstractmethod
    def choose_turn(self, board: Board, stone_count: int, time_left: float) -> list[Position]:
        raise NotImplementedError


class HumanPlayer(Player):
    """Marker player. The Tk interface collects and submits this player's full turn."""

    def choose_turn(self, board: Board, stone_count: int, time_left: float) -> list[Position]:
        raise RuntimeError("真人玩家应通过棋盘界面落子")


class HeuristicPlayer(Player):
    """Fast baseline AI: wins, blocks, then builds lines near existing stones."""

    def candidate_positions(self, board: Board) -> list[Position]:
        occupied = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board.get(r, c) != EMPTY]
        if not occupied:
            return [(BOARD_SIZE // 2, BOARD_SIZE // 2)]
        candidates: set[Position] = set()
        for row, col in occupied:
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    pos = row + dr, col + dc
                    if board.is_empty(*pos):
                        candidates.add(pos)
        return list(candidates) or board.empty_positions()

    @staticmethod
    def positional_score(board: Board, pos: Position, color: int) -> float:
        trial = board.copy()
        trial.place(*pos, color)
        own = max(line_length(trial, pos, color, *direction) for direction in DIRECTIONS)
        foe = opponent(color)
        block_trial = board.copy()
        block_trial.place(*pos, foe)
        threat = max(line_length(block_trial, pos, foe, *direction) for direction in DIRECTIONS)
        center = BOARD_SIZE - (abs(pos[0] - 9) + abs(pos[1] - 9))
        own_weights = {1: 2, 2: 20, 3: 180, 4: 1800, 5: 30000, 6: 1_000_000}
        foe_weights = {1: 1, 2: 18, 3: 220, 4: 2400, 5: 100_000, 6: 900_000}
        return own_weights.get(min(own, 6), 0) + foe_weights.get(min(threat, 6), 0) + center + random.random()

    def choose_turn(self, board: Board, stone_count: int, time_left: float) -> list[Position]:
        assert self.color is not None
        result: list[Position] = []
        working = board.copy()
        for _ in range(min(stone_count, len(working.empty_positions()))):
            candidates = self.candidate_positions(working)
            move = max(candidates, key=lambda pos: self.positional_score(working, pos, self.color))
            result.append(move)
            working.place(*move, self.color)
        return result


class RandomPlayer(Player):
    def choose_turn(self, board: Board, stone_count: int, time_left: float) -> list[Position]:
        return random.sample(board.empty_positions(), min(stone_count, len(board.empty_positions())))
