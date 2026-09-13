from __future__ import annotations

from .board import Board, Position
from .constants import BLACK, WHITE, WIN_LENGTH

# 六子只可能出现在横、竖、主对角线和副对角线四条轴线上。
DIRECTIONS = ((0, 1), (1, 0), (1, 1), (1, -1))


def line_length(board: Board, position: Position, color: int, dr: int, dc: int) -> int:
    """统计经过指定落点、沿一个方向延伸的连续同色棋子数。"""
    row, col = position
    total = 1
    # 从落点向正、反两个方向扫描；遇到边界或异色棋子立即停止。
    for sign in (-1, 1):
        r, c = row + sign * dr, col + sign * dc
        while Board.inside(r, c) and board.get(r, c) == color:
            total += 1
            r += sign * dr
            c += sign * dc
    return total


def has_won(board: Board, color: int, positions: list[Position]) -> bool:
    """只检查本回合的新落点，因为旧棋形不会在本回合自行成六。"""
    if color not in (BLACK, WHITE):
        raise ValueError(f"无效的棋子颜色：{color}")
    return any(
        line_length(board, pos, color, dr, dc) >= WIN_LENGTH
        for pos in positions
        for dr, dc in DIRECTIONS
    )


def validate_turn(board: Board, moves: list[Position], expected: int) -> None:
    """原子校验一整手棋，不在校验失败时污染真实棋盘。"""
    if not isinstance(board, Board):
        raise TypeError("board 必须是 Board 对象")
    if expected not in (1, 2):
        raise ValueError("每回合的棋子数只能是 1 或 2")
    if not isinstance(moves, list):
        raise ValueError("落点必须使用列表一次性提交")
    if any(
        not isinstance(move, tuple)
        or len(move) != 2
        or not all(isinstance(value, int) and not isinstance(value, bool) for value in move)
        for move in moves
    ):
        raise ValueError("每个落点必须是由两个整数组成的坐标")
    if len(moves) != expected:
        raise ValueError(f"本回合必须提交 {expected} 颗棋子")
    if len(set(moves)) != len(moves):
        raise ValueError("同一回合的落点不能重复")
    # 在副本上依次试放，可同时发现越界和已占用位置。
    candidate = board.copy()
    for row, col in moves:
        candidate.place(row, col, BLACK)


def commit_turn(board: Board, moves: list[Position], color: int) -> Board:
    """把已经确定的一组落点提交到新棋盘，原棋盘保持不变。"""
    if color not in (BLACK, WHITE):
        raise ValueError(f"无效的棋子颜色：{color}")
    result = board.copy()
    for row, col in moves:
        result.place(row, col, color)
    return result
