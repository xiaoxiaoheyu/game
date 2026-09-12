from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from enum import Enum

from .board import Board, Position, format_position
from .clock import ChessClock
from .constants import BLACK, WHITE, COLOR_NAMES, opponent
from .players import Player
from .rules import commit_turn, has_won, validate_turn


class GameStatus(str, Enum):
    RUNNING = "RUNNING"
    BLACK_WIN = "BLACK_WIN"
    WHITE_WIN = "WHITE_WIN"
    DRAW = "DRAW"
    TIMEOUT = "TIMEOUT"


@dataclass
class TurnRecord:
    turn: int
    color: int
    moves: list[Position]
    time_left: float

    def as_dict(self) -> dict:
        return {"turn": self.turn, "color": COLOR_NAMES[self.color], "moves": [format_position(p) for p in self.moves], "time_left": round(self.time_left, 3)}


@dataclass
class Game:
    player_a: Player
    player_b: Player
    total_time: float = 300.0
    board: Board = field(default_factory=Board)
    current_color: int = BLACK
    turn_number: int = 1
    status: GameStatus = GameStatus.RUNNING
    winner: int | None = None
    last_moves: list[Position] = field(default_factory=list)
    records: list[TurnRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if secrets.randbelow(2) == 0:
            self.players = {BLACK: self.player_a, WHITE: self.player_b}
        else:
            self.players = {BLACK: self.player_b, WHITE: self.player_a}
        for color, player in self.players.items():
            player.on_game_start(color)
        self.clocks = {BLACK: ChessClock(self.total_time), WHITE: ChessClock(self.total_time)}

    @property
    def expected_stones(self) -> int:
        return 1 if self.turn_number == 1 else min(2, len(self.board.empty_positions()))

    def start_current_clock(self) -> None:
        self.clocks[self.current_color].start()

    def check_timeout(self) -> bool:
        if self.clocks[self.current_color].expired():
            self.clocks[self.current_color].stop()
            self.status = GameStatus.TIMEOUT
            self.winner = opponent(self.current_color)
            return True
        return False

    def submit_turn(self, moves: list[Position]) -> None:
        if self.status != GameStatus.RUNNING:
            raise ValueError("对局已经结束")
        if self.check_timeout():
            raise TimeoutError("棋钟超时")
        validate_turn(self.board, moves, self.expected_stones)
        self.board = commit_turn(self.board, moves, self.current_color)
        self.last_moves = moves[:]
        self.clocks[self.current_color].stop()
        self.records.append(TurnRecord(self.turn_number, self.current_color, moves[:], self.clocks[self.current_color].remaining()))
        if has_won(self.board, self.current_color, moves):
            self.winner = self.current_color
            self.status = GameStatus.BLACK_WIN if self.current_color == BLACK else GameStatus.WHITE_WIN
            return
        if self.board.is_full():
            self.status = GameStatus.DRAW
            return
        previous = self.current_color
        self.current_color = opponent(self.current_color)
        self.turn_number += 1
        self.players[self.current_color].on_opponent_turn(moves)

