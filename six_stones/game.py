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
        """转换为可直接写入 JSON 对局日志的结构。"""
        return {
            "turn": self.turn,
            "color": COLOR_NAMES[self.color],
            "moves": [format_position(position) for position in self.moves],
            "time_left": round(self.time_left, 3),
        }


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
        """校验开局参数，再使用安全随机数分配黑白双方。"""
        if not isinstance(self.player_a, Player) or not isinstance(self.player_b, Player):
            raise TypeError("对局双方必须是 Player 对象")
        if self.player_a is self.player_b:
            raise ValueError("对局双方不能使用同一个棋手对象")
        if not isinstance(self.board, Board):
            raise TypeError("board 必须是 Board 对象")
        if self.current_color not in (BLACK, WHITE):
            raise ValueError("当前行棋颜色无效")
        if not isinstance(self.turn_number, int) or self.turn_number < 1:
            raise ValueError("回合编号必须是正整数")

        # 先构造棋钟完成时间校验，避免开局失败后仍修改棋手的颜色。
        self.clocks = {
            BLACK: ChessClock(self.total_time),
            WHITE: ChessClock(self.total_time),
        }

        # 黑白归属在每盘开局独立随机，双方程序获得结果后再开始行棋。
        if secrets.randbelow(2) == 0:
            self.players = {BLACK: self.player_a, WHITE: self.player_b}
        else:
            self.players = {BLACK: self.player_b, WHITE: self.player_a}
        for color, player in self.players.items():
            player.color = color

    @property
    def expected_stones(self) -> int:
        """首回合黑方下一颗；之后下两颗，末盘不足两格时按余量计算。"""
        return 1 if self.turn_number == 1 else min(2, len(self.board.empty_positions()))

    def start_current_clock(self) -> None:
        self.clocks[self.current_color].start()

    def check_timeout(self) -> bool:
        """结算当前棋手是否超时，并在超时时立即判对方获胜。"""
        if self.clocks[self.current_color].expired():
            self.clocks[self.current_color].stop()
            self.status = GameStatus.TIMEOUT
            self.winner = opponent(self.current_color)
            return True
        return False

    def submit_turn(self, moves: list[Position]) -> None:
        """一次性校验并提交整手棋，然后判断胜负并切换行棋方。"""
        if self.status != GameStatus.RUNNING:
            raise ValueError("对局已经结束")
        if self.check_timeout():
            raise TimeoutError("棋钟超时")
        validate_turn(self.board, moves, self.expected_stones)
        # commit_turn 返回新棋盘，保证两颗棋子要么全部成功，要么都不落下。
        self.board = commit_turn(self.board, moves, self.current_color)
        self.last_moves = moves[:]
        self.clocks[self.current_color].stop()
        self.records.append(
            TurnRecord(
                self.turn_number,
                self.current_color,
                moves[:],
                self.clocks[self.current_color].remaining(),
            )
        )
        if has_won(self.board, self.current_color, moves):
            self.winner = self.current_color
            self.status = GameStatus.BLACK_WIN if self.current_color == BLACK else GameStatus.WHITE_WIN
            return
        if self.board.is_full():
            self.status = GameStatus.DRAW
            return
        self.current_color = opponent(self.current_color)
        self.turn_number += 1
