from __future__ import annotations

from .board import Board, Position
from .constants import WIN_LENGTH

DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def line_length(board: Board, position: Position, color: int, dr: int, dc: int) -> int:
    row, col = position
    total = 1
    for sign in (-1, 1):
        r, c = row + sign * dr, col + sign * dc
        while Board.inside(r, c) and board.get(r, c) == color:
            total += 1
            r += sign * dr
            c += sign * dc
    return total


def has_won(board: Board, color: int, positions: list[Position]) -> bool:
    return any(
        line_length(board, pos, color, dr, dc) >= WIN_LENGTH
        for pos in positions
        for dr, dc in DIRECTIONS
    )


def validate_turn(board: Board, moves: list[Position], expected: int) -> None:
    if len(moves) != expected:
        raise ValueError(f"本回合必须提交 {expected} 颗棋子")
    if len(set(moves)) != len(moves):
        raise ValueError("同一回合的落点不能重复")
    candidate = board.copy()
    for row, col in moves:
        candidate.place(row, col, 1)


def commit_turn(board: Board, moves: list[Position], color: int) -> Board:
    result = board.copy()
    for row, col in moves:
        result.place(row, col, color)
    return result
